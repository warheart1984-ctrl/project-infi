import type { InvariantSet, ThresholdDelta } from "../css2/types";
import { mergeThreshold } from "../css2/types";
import { checkNonDerogableViolations } from "./invariants";

export interface RecalibrationGuardResult {
  allowed: boolean;
  violatedInvariants: string[];
  reason?: string;
}

export function enforceCRKOnThresholdDelta(
  delta: ThresholdDelta,
  invSet: InvariantSet,
): RecalibrationGuardResult {
  const after = mergeThreshold(delta.before, delta.after);
  const violations = checkNonDerogableViolations(invSet, delta.before, after);
  if (violations.length > 0) {
    return {
      allowed: false,
      violatedInvariants: violations.map((v) => v.id),
      reason: "Non-derogable invariant violation",
    };
  }
  return { allowed: true, violatedInvariants: [] };
}
