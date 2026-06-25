import { invariantEngine } from "../invariants/engine";
import { constraintEngine } from "./constraint-engine";
import { clusterView } from "../cluster/macc";

export interface DLAPResult {
  ok: boolean;
  reason?: string;
  detail?: unknown;
}

export function dLAP(
  action: { type: string; payload?: Record<string, unknown> },
  context: Record<string, unknown>
): DLAPResult {
  const clusterState = clusterView();

  const local = invariantEngine.checkAll(action, context);
  if (!local.ok) {
    return { ok: false, reason: "local-invariant", detail: local };
  }

  const cluster = checkClusterInvariants(action, clusterState);
  if (!cluster.ok) {
    return { ok: false, reason: "cluster-invariant", detail: cluster };
  }

  const constraints = constraintEngine.check(action, context, clusterState);
  if (!constraints.ok) {
    return { ok: false, reason: "constraint", detail: constraints };
  }

  return { ok: true };
}

function checkClusterInvariants(
  _action: { type: string },
  _clusterState: ReturnType<typeof clusterView>
): { ok: boolean } {
  return { ok: true };
}
