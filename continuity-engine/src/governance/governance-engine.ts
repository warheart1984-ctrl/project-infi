import type {
  InvariantSet,
  RecalibrationDecision,
  RecalibrationEvent,
  Threshold,
  ThresholdDelta,
} from "../css2/types";
import { mergeThreshold } from "../css2/types";
import { enforceCRKOnThresholdDelta } from "../crk1/recalibration-guard";
import { runAdversarialReview } from "./adversarial-review";
import { scoreLegitimacy } from "./legitimacy";

export interface GovernanceContext {
  delta: ThresholdDelta;
  invSet: InvariantSet;
  evidence: unknown[];
  scope?: RecalibrationEvent["scope"];
  triggerType?: RecalibrationEvent["triggerType"];
  failureModeBefore?: RecalibrationEvent["failureModeBefore"];
  decidedBy?: string;
}

export class RecalibrationGovernanceEngine {
  async evaluate(ctx: GovernanceContext): Promise<RecalibrationEvent> {
    const now = new Date().toISOString();
    const before = ctx.delta.before;
    const after = mergeThreshold(before, ctx.delta.after);

    const crkResult = enforceCRKOnThresholdDelta(ctx.delta, ctx.invSet);
    const adversarial = runAdversarialReview(ctx.delta, ctx.evidence);
    const legitimacy = scoreLegitimacy(crkResult.allowed, adversarial.passed, ctx.evidence.length);

    let decision: RecalibrationDecision = legitimacy.decision;
    let legitimacyBasis = legitimacy.basis;

    if (!crkResult.allowed) {
      decision = "rejected";
      const invDesc = crkResult.violatedInvariants.join(", ");
      legitimacyBasis = `Proposed threshold violates non-derogable invariant(s): ${invDesc}. ${crkResult.reason ?? ""}`.trim();
    } else if (!adversarial.passed) {
      decision = "deferred";
      legitimacyBasis = `Adversarial review incomplete: ${adversarial.notes.join("; ")}`;
    }

    return {
      eventId: ctx.delta.recalibrationEventId ?? `recal-${Date.now()}`,
      timestamp: now,
      scope: ctx.scope ?? "subsystem",
      triggerType: ctx.triggerType ?? "failure",
      failureModeBefore: ctx.failureModeBefore,
      proposedChanges: [
        {
          id: before.id,
          before,
          after,
          rationale: ctx.delta.rationale,
        },
      ],
      invariantsChecked: ctx.invSet.invariants,
      decision,
      legitimacyBasis,
      continuityEffect: decision === "approved" ? "improved" : "degraded",
      decidedBy: ctx.decidedBy ?? "WhiteTeam:ContinuityCouncil",
    };
  }
}

export function buildRecalibrationProposal(
  threshold: Threshold,
  newValue: unknown,
  rationale: string,
): ThresholdDelta {
  return {
    thresholdId: threshold.id,
    before: threshold,
    after: { value: newValue },
    rationale,
  };
}
