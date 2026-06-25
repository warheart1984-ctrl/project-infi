import { createHash } from "crypto";
import type { Snapshot } from "./substrate";

export interface PITTransition {
  from: number;
  to: number;
  ts: number;
}

export interface CRP {
  snapshotId: string;
  receipts: unknown[];
  pitTransitions: PITTransition[];
  hash: string;
}

export function generateCRP(
  snapshot: Snapshot,
  receipts: unknown[],
  pitTransitions: PITTransition[]
): CRP {
  const hash = createHash("sha256")
    .update(JSON.stringify({ snapshot, receipts, pitTransitions }))
    .digest("hex");
  return { snapshotId: snapshot.id, receipts, pitTransitions, hash };
}
