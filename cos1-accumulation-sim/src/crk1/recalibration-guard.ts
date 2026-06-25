import type { ThresholdDelta } from "../css2/types.js";
import type { InvariantSet } from "./invariants.js";

export interface CRKGuardResult {
  allowed: boolean;
  reason: string;
}

export function enforceCRKOnThresholdDelta(
  delta: ThresholdDelta,
  invariants: InvariantSet,
): CRKGuardResult {
  const blocked = delta.affectsInvariants.filter((id) => {
    const w = invariants.weights[id];
    return w !== undefined && w >= 0.85;
  });

  if (blocked.length > 0) {
    return {
      allowed: false,
      reason: `Non-derogable invariants touched: ${blocked.join(", ")}`,
    };
  }

  if (!invariants.ids.some((id) => delta.affectsInvariants.includes(id))) {
    return { allowed: true, reason: "No constitutional invariants implicated" };
  }

  return { allowed: true, reason: "CRK-1 guard passed" };
}
