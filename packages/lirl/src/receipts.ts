import {
  createEvidenceReceipt,
  ReceiptStore,
  type EvidenceReceipt,
  type StoredReceipt,
} from '@aaes-os/evidence-receipts';

import type { LirlIntent, LirlVerdict } from './types.js';

export interface LirlReceiptSubject {
  intentId: string;
  verdict: LirlVerdict;
  actorId: string;
  action: string;
  reasons: string[];
  memoryWritten: boolean;
  memoryKey?: string;
  runId: string;
  spanId: string;
}

export class LirlReceiptService {
  readonly store = new ReceiptStore();

  issue(subject: LirlReceiptSubject, intent: LirlIntent): EvidenceReceipt & { stored: StoredReceipt } {
    const receipt = createEvidenceReceipt({
      claimLabel: `lirl:${subject.verdict.toLowerCase()}:${intent.action}`,
      subsystem: 'lirl-vertical-slice',
      evidenceRefs: [subject.intentId, subject.runId, subject.spanId],
      subject,
      kind: subject.verdict === 'ACCEPT' ? 'runtime' : 'fault',
    });

    const stored = this.store.add({
      ...receipt,
      receiptId: receipt.receiptId,
      issuedAt: receipt.issuedAt,
      verdict: subject.verdict,
      intentId: subject.intentId,
      actorId: subject.actorId,
      action: subject.action,
      memoryWritten: subject.memoryWritten,
      reasons: subject.reasons,
    });

    return { ...receipt, stored };
  }

  latest(): StoredReceipt | null {
    return this.store.getLatest();
  }

  getById(id: string): StoredReceipt | undefined {
    return this.store.getById(id);
  }
}
