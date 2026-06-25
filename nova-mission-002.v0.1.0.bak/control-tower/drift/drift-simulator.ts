export type DriftType =
  | "ledger"
  | "continuity"
  | "pit"
  | "invariant"
  | "constraint"
  | "dlap";

export function simulateDrift(
  agentA: string,
  agentB: string,
  type: DriftType
): { agentA: string; agentB: string; type: DriftType; introduced: boolean } {
  return { agentA, agentB, type, introduced: true };
}

export function correctDrift<T extends { id: string }>(
  cluster: T[],
  canonical: T
): T[] {
  return cluster.map((agent) => ({ ...agent, ...canonical }));
}
