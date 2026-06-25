import { createHash, randomUUID } from "crypto";

export interface Snapshot {
  id: string;
  hash: string;
  partial: boolean;
  state: Record<string, unknown>;
  ts: number;
}

const store: Snapshot[] = [];

function hashState(state: Record<string, unknown>): string {
  return createHash("sha256").update(JSON.stringify(state)).digest("hex");
}

export function takeSnapshot(state: Record<string, unknown>, partial = false): Snapshot {
  const hash = hashState(state);
  const snapshot: Snapshot = {
    id: randomUUID(),
    hash,
    partial,
    state,
    ts: Date.now(),
  };
  store.push(snapshot);
  return snapshot;
}

export function listSnapshots(): Snapshot[] {
  return [...store];
}

export function replay(snapshotId: string): Record<string, unknown> | null {
  const snapshot = store.find((s) => s.id === snapshotId);
  return snapshot?.state ?? null;
}
