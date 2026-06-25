export { snapshot, replay, getSnapshots, getContinuityHash, updateContinuity } from "./substrate";

export async function diff(
  a: import("./substrate").Snapshot,
  b: import("./substrate").Snapshot
): Promise<{ from: string; to: string; changed: boolean }> {
  return {
    from: a.stateHash,
    to: b.stateHash,
    changed: a.stateHash !== b.stateHash,
  };
}
