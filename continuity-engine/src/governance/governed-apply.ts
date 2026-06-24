import type { InvariantSet, Threshold, ThresholdDelta } from "../css2/types";
import {
  assessLegitimateJudgment,
  buildLegitimateJudgmentInputFromGovernanceContext,
} from "../crk1/legitimate-judgment";
import { enforceCRKOnThresholdDelta } from "../crk1/recalibration-guard";
import type { JudgmentCapabilityAssessment } from "../jpa1/judgment-capability";
import type { JudgmentCycle } from "../judgment/cycle";
import type { ThresholdRegistry } from "../registry/threshold-registry";

export interface GovernedApplyResult {
  applied: boolean;
  threshold?: Threshold;
  violatedInvariants?: string[];
  reason?: string;
  legitimate?: boolean;
  crk1jGaps?: string[];
}

export interface GovernedApplyOptions {
  evidence?: unknown[];
  judgmentAssessment?: JudgmentCapabilityAssessment;
  observerCaptured?: boolean;
  requireJudgmentAssessment?: boolean;
  judgmentCycle?: JudgmentCycle;
}

export async function applyDeltaWithCRKGuard(
  registry: ThresholdRegistry,
  delta: ThresholdDelta,
  actorId: string,
  invSet: InvariantSet,
  options: GovernedApplyOptions = {},
): Promise<GovernedApplyResult> {
  const guard = enforceCRKOnThresholdDelta(delta, invSet);
  if (!guard.allowed) {
    return {
      applied: false,
      violatedInvariants: guard.violatedInvariants,
      reason: guard.reason,
      legitimate: false,
    };
  }

  const evidence = options.evidence ?? [];
  const crk1jInput = buildLegitimateJudgmentInputFromGovernanceContext(
    {
      delta,
      evidence,
      judgmentAssessment: options.judgmentAssessment,
      observerCaptured: options.observerCaptured,
      requireJudgmentAssessment: options.requireJudgmentAssessment,
      judgmentCycle: options.judgmentCycle,
    },
    guard.allowed,
  );
  const crk1j = assessLegitimateJudgment(crk1jInput);
  if (!crk1j.legitimate) {
    return {
      applied: false,
      reason: `CRK-1.J: ${crk1j.gaps.join("; ")}`,
      legitimate: false,
      crk1jGaps: crk1j.gaps,
    };
  }

  const threshold = await registry.applyDelta(delta, actorId);
  return { applied: true, threshold, legitimate: true };
}
