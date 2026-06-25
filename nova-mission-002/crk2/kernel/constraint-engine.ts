import type { ClusterState } from "../cluster/macc";

export interface ConstraintCheckResult {
  ok: boolean;
  constraintId?: string;
}

export const constraintEngine = {
  check(
    _action: { type: string },
    _context: Record<string, unknown>,
    _clusterState: ClusterState
  ): ConstraintCheckResult {
    return { ok: true };
  },
};
