import type { ThresholdDelta } from "../css2/types.js";
import type { InvariantSet } from "../crk1/invariants.js";
import { enforceCRKOnThresholdDelta } from "../crk1/recalibration-guard.js";
import {
  assessJudgmentLegitimacy,
  type JudgmentGovernanceContext,
} from "./judgment-governance.js";

export interface GovernanceInputs {
  delta: ThresholdDelta;
  invariants: InvariantSet;
  judgmentContext: JudgmentGovernanceContext;
}

export interface GovernanceDecision {
  allowed: boolean;
  reasons: string[];
}

export function evaluateThresholdDeltaWithJudgment(
  inputs: GovernanceInputs,
): GovernanceDecision {
  const { delta, invariants, judgmentContext } = inputs;

  const crkResult = enforceCRKOnThresholdDelta(delta, invariants);
  const judgmentResult = assessJudgmentLegitimacy(judgmentContext);

  const reasons: string[] = [];

  if (!crkResult.allowed) {
    reasons.push(`CRK-1 invariants violated: ${crkResult.reason}`);
  }

  if (!judgmentResult.passesMinimumStandard) {
    reasons.push(
      `JPA-1 judgment standard not met: ${judgmentResult.reasons.join("; ")}`,
    );
  }

  const allowed = crkResult.allowed && judgmentResult.passesMinimumStandard;

  return { allowed, reasons };
}
