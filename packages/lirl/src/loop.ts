import { randomUUID } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import { LirlLawGate } from './lawGate.js';
import { GovernedMemoryStore } from './memory.js';
import { buildOperatorSnapshot } from './operatorView.js';
import { LirlReceiptService } from './receipts.js';
import type { LirlIntent, LirlLoopResult } from './types.js';

export interface LirlRuntimeOptions {
  /** Root for memory + operator HTML (default: .runtime/lirl under cwd). */
  runtimeRoot?: string;
}

export class LirlRuntime {
  readonly gate: LirlLawGate;
  readonly memory: GovernedMemoryStore;
  readonly receipts: LirlReceiptService;
  readonly runtimeRoot: string;
  readonly operatorHtmlPath: string;

  constructor(options: LirlRuntimeOptions = {}) {
    this.runtimeRoot = options.runtimeRoot ?? path.resolve(process.cwd(), '.runtime', 'lirl');
    mkdirSync(this.runtimeRoot, { recursive: true });
    this.gate = new LirlLawGate();
    this.memory = new GovernedMemoryStore(path.join(this.runtimeRoot, 'memory'));
    this.receipts = new LirlReceiptService();
    this.operatorHtmlPath = path.join(this.runtimeRoot, 'operator.html');
  }

  /**
   * Lawful Intent Receipt Loop:
   * intent → law gate → memory write (accept only) → receipt → operator view
   */
  async processIntent(rawIntent: LirlIntent): Promise<LirlLoopResult> {
    const intentId = rawIntent.intentId?.trim() || randomUUID();
    const intent: LirlIntent = { ...rawIntent, intentId };

    const gate = await this.gate.evaluate(intent);
    const accepted = gate.verdict === 'ACCEPT';

    if (!accepted) {
      const issued = this.receipts.issue(
        {
          intentId,
          verdict: 'REJECT',
          actorId: intent.actorId || '',
          action: intent.action || '',
          reasons: gate.reasons,
          memoryWritten: false,
          runId: gate.runId,
          spanId: gate.spanId,
        },
        intent,
      );

      const operatorView = buildOperatorSnapshot({
        verdict: 'REJECT',
        receiptId: issued.receiptId,
        intentId,
        actorId: intent.actorId || '',
        action: intent.action || '',
        memoryWritten: false,
        reasons: gate.reasons,
        issuedAt: issued.issuedAt,
      });
      this.writeOperatorHtml(operatorView.html);

      return {
        intentId,
        verdict: 'REJECT',
        reasons: gate.reasons,
        runId: gate.runId,
        spanId: gate.spanId,
        receiptId: issued.receiptId,
        memoryWritten: false,
        operatorView,
      };
    }

    // ACCEPT path
    const memoryKey =
      intent.action === 'memory.write' ? String(intent.payload?.key) : undefined;

    const issued = this.receipts.issue(
      {
        intentId,
        verdict: 'ACCEPT',
        actorId: intent.actorId,
        action: intent.action,
        reasons: [],
        memoryWritten: intent.action === 'memory.write',
        memoryKey,
        runId: gate.runId,
        spanId: gate.spanId,
      },
      intent,
    );

    let memoryWritten = false;
    if (intent.action === 'memory.write') {
      this.memory.write({
        key: String(intent.payload?.key),
        value: intent.payload?.value,
        writtenAt: new Date().toISOString(),
        intentId,
        actorId: intent.actorId,
        receiptId: issued.receiptId,
      });
      memoryWritten = true;
    }

    const operatorView = buildOperatorSnapshot({
      verdict: 'ACCEPT',
      receiptId: issued.receiptId,
      intentId,
      actorId: intent.actorId,
      action: intent.action,
      memoryWritten,
      reasons: [],
      issuedAt: issued.issuedAt,
    });
    this.writeOperatorHtml(operatorView.html);

    return {
      intentId,
      verdict: 'ACCEPT',
      reasons: [],
      runId: gate.runId,
      spanId: gate.spanId,
      receiptId: issued.receiptId,
      memoryWritten,
      memoryKey,
      operatorView,
    };
  }

  private writeOperatorHtml(html: string): void {
    writeFileSync(this.operatorHtmlPath, html, 'utf8');
  }
}

export async function processLirlIntent(
  intent: LirlIntent,
  options?: LirlRuntimeOptions,
): Promise<LirlLoopResult> {
  return new LirlRuntime(options).processIntent(intent);
}
