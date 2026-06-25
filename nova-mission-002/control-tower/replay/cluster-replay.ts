export interface ClusterReplayRequest {
  agentIds: string[];
  fromSnapshotId?: string;
  toSnapshotId?: string;
}

export interface DivergenceEvent {
  id: string;
  type: "ledger" | "continuity" | "pit" | "invariant";
  snapshotId?: string;
  agents: string[];
}

export interface ClusterReplayResult {
  perAgent: Record<
    string,
    { snapshots: unknown[]; receipts: unknown[]; pitTransitions: unknown[] }
  >;
  divergences: DivergenceEvent[];
}

export async function replayCluster(req: ClusterReplayRequest): Promise<ClusterReplayResult> {
  const perAgent: ClusterReplayResult["perAgent"] = {};
  for (const id of req.agentIds) {
    perAgent[id] = { snapshots: [], receipts: [], pitTransitions: [] };
  }
  return { perAgent, divergences: [] };
}
