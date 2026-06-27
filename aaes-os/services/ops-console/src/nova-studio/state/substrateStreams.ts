import type { SkillzMcgeeLedgerSummary, SkillzMcgeeReceipt } from './studioState.js';

export type TimelineEvent = {
  id: string;
  label: string;
  timestamp: string;
};

export type LineageDelta = {
  from: string;
  to: string;
  label: string;
};

export type ReplayCheckpoint = {
  id: string;
  receiptId: string;
  status: string;
};

export type SubstrateSnapshot = {
  receipts: SkillzMcgeeReceipt[];
  timeline: TimelineEvent[];
  lineage: LineageDelta[];
  replayCheckpoints: ReplayCheckpoint[];
};

export function createSubstrateSnapshot(summary: SkillzMcgeeLedgerSummary): SubstrateSnapshot {
  return {
    receipts: summary.recentReceipts,
    timeline: summary.recentReceipts.map((receipt) => ({
      id: receipt.id,
      label: `${receipt.slice}:${receipt.status}`,
      timestamp: receipt.timestamp,
    })),
    lineage: summary.recentReceipts.slice(1).map((receipt, index) => ({
      from: summary.recentReceipts[index].id,
      to: receipt.id,
      label: 'receipt-lineage',
    })),
    replayCheckpoints: summary.recentReceipts.map((receipt) => ({
      id: `checkpoint:${receipt.id}`,
      receiptId: receipt.id,
      status: receipt.status,
    })),
  };
}
