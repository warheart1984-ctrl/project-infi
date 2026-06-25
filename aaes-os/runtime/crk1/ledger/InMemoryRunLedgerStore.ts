import { createHash } from 'node:crypto';

import type { InvariantResult } from '../governance/types.js';
import type { Fault, Receipt, RunContext } from '../types.js';
import type { RunLedgerStore } from './RunLedgerStore.js';

function receiptHash(ctx: RunContext, result: unknown): string {
  const payload = JSON.stringify({
    runId: ctx.id,
    payload: ctx.payload,
    spans: ctx.spans.map((s) => ({ type: s.type, data: s.data })),
    result,
  });
  return createHash('sha256').update(payload).digest('hex');
}

export class InMemoryRunLedgerStore implements RunLedgerStore {
  private readonly receipts = new Map<string, Receipt>();
  private readonly faults = new Map<string, Fault>();

  async recordReceipt(ctx: RunContext, result: unknown): Promise<Receipt> {
    const receipt: Receipt = {
      runId: ctx.id,
      hash: receiptHash(ctx, result),
      spans: [...ctx.spans],
      result,
      createdAt: new Date().toISOString(),
    };
    this.receipts.set(ctx.id, receipt);
    return receipt;
  }

  async recordFault(ctx: RunContext, fault: InvariantResult): Promise<Fault> {
    const record: Fault = {
      runId: ctx.id,
      invariantId: fault.invariantId ?? 'INV.UNKNOWN',
      message: fault.message ?? 'Invariant violation',
      timestamp: new Date().toISOString(),
    };
    this.faults.set(ctx.id, record);
    return record;
  }

  getReceipt(runId: string): Receipt | undefined {
    return this.receipts.get(runId);
  }

  getFault(runId: string): Fault | undefined {
    return this.faults.get(runId);
  }

  listReceipts(): Receipt[] {
    return [...this.receipts.values()];
  }

  listFaults(): Fault[] {
    return [...this.faults.values()];
  }
}
