import { sha256 } from "../lib/hash";
import { uuid } from "../lib/uuid";
import { getContext } from "../runtime/workspace";

export interface Snapshot {
  id: string;
  timestamp: number;
  stateHash: string;
}

const snapshots: Snapshot[] = [];
let currentStateHash = "initial";

export async function computeWorkspaceHash(): Promise<string> {
  const ctx = await getContext();
  const payload = JSON.stringify({ root: ctx.root, files: ctx.files.sort() });
  return sha256(payload);
}

export async function getContinuityHash(): Promise<string> {
  return currentStateHash;
}

export async function snapshot(): Promise<Snapshot> {
  const stateHash = await computeWorkspaceHash();
  const snap: Snapshot = {
    id: uuid(),
    timestamp: Date.now(),
    stateHash,
  };
  snapshots.push(snap);
  currentStateHash = stateHash;
  return snap;
}

export function getSnapshots(): readonly Snapshot[] {
  return snapshots;
}

export async function updateContinuity(_action: import("../types/actions").AgentAction): Promise<void> {
  currentStateHash = await computeWorkspaceHash();
}

export async function replay(id: string): Promise<{ snapshot: Snapshot | null; receipts: import("../types/receipts").GovernanceReceipt[] }> {
  const snap = snapshots.find((s) => s.id === id) ?? null;
  const { getLedger } = await import("../governance/ledger");
  return { snapshot: snap, receipts: [...getLedger()] };
}
