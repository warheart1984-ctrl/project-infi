import type { InvariantSet, Threshold, ThresholdDelta } from "../css2/types";
import { enforceCRKOnThresholdDelta } from "../crk1/recalibration-guard";
import type { ThresholdRegistry } from "../registry/threshold-registry";

export interface GovernedApplyResult {
  applied: boolean;
  threshold?: Threshold;
  violatedInvariants?: string[];
  reason?: string;
}

export async function applyDeltaWithCRKGuard(
  registry: ThresholdRegistry,
  delta: ThresholdDelta,
  actorId: string,
  invSet: InvariantSet,
): Promise<GovernedApplyResult> {
  const guard = enforceCRKOnThresholdDelta(delta, invSet);
  if (!guard.allowed) {
    return {
      applied: false,
      violatedInvariants: guard.violatedInvariants,
      reason: guard.reason,
    };
  }

  const threshold = await registry.applyDelta(delta, actorId);
  return { applied: true, threshold };
}
