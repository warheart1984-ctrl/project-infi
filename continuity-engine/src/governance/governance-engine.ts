import type {
  InvariantSet,
  LegitimateJudgmentSummary,
  RecalibrationDecision,
  RecalibrationEvent,
  Threshold,
  ThresholdDelta,
} from "../css2/types";
import { mergeThreshold } from "../css2/types";
import {
  assessLegitimateJudgment,
  buildLegitimateJudgmentInputFromGovernanceContext,
  recalibrationDecisionFromLegitimateJudgment,
} from "../crk1/legitimate-judgment";
import type { JudgmentCapabilityAssessment } from "../jpa1/judgment-capability";
import type { JudgmentCycle } from "../judgment/cycle";
import type { RealityVetoReceipt } from "../rpa1/reality-veto";
import { escalateIgnoredVeto } from "../rpa1/reality-veto";
import { applyGovernanceWithRealityVeto } from "./reality-veto";
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
  /** JPA-1 / OPA-1 — observer judgment assessment for CRK-1.J gate. */
  judgmentAssessment?: JudgmentCapabilityAssessment;
  /** Steward captured — blocks stewardship accountability (CRK-1.J). */
  observerCaptured?: boolean;
  /** When true, Δ-threshold approval requires explicit judgment assessment. */
  requireJudgmentAssessment?: boolean;
  /** CRK-1.J.5 — judgment cycle for corrigibility gate. */
  judgmentCycle?: JudgmentCycle;
  /** RPA-1 — active or ignored Reality Veto receipt. */
  realityVeto?: RealityVetoReceipt;
  /** Steward ignored a mandatory veto reconsideration. */
  realityVetoIgnored?: boolean;
}

function toLegitimateJudgmentSummary(
  result: ReturnType<typeof assessLegitimateJudgment>,
): LegitimateJudgmentSummary {
  return {
    legitimate: result.legitimate,
    category: result.category,
    satisfiedRequirements: result.satisfiedRequirements,
    failedRequirements: result.failedRequirements,
    gaps: result.gaps,
  };
}

export class RecalibrationGovernanceEngine {
  async evaluate(ctx: GovernanceContext): Promise<RecalibrationEvent> {
    const now = new Date().toISOString();
    const before = ctx.delta.before;
    const after = mergeThreshold(before, ctx.delta.after);

    const crkResult = enforceCRKOnThresholdDelta(ctx.delta, ctx.invSet);
    const adversarial = runAdversarialReview(ctx.delta, ctx.evidence);

    const vetoEscalation = ctx.realityVeto
      ? escalateIgnoredVeto(ctx.realityVeto, {
          ignored: ctx.realityVetoIgnored,
          suppressed: ctx.realityVeto.suppressed,
        })
      : null;

    if (ctx.judgmentCycle) {
      const corrigibilityGate = applyGovernanceWithRealityVeto(ctx.judgmentCycle, {
        allowed: true,
        reasons: [],
      });
      if (!corrigibilityGate.allowed) {
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
          decision: "rejected",
          legitimacyBasis: corrigibilityGate.reasons.join("; "),
          legitimateJudgment: {
            legitimate: false,
            category: "CRK-1.J",
            satisfiedRequirements: [],
            failedRequirements: ["corrigibility"],
            gaps: corrigibilityGate.reasons,
          },
          continuityEffect: "degraded",
          decidedBy: ctx.decidedBy ?? "WhiteTeam:ContinuityCouncil",
        };
      }
    }

    const crk1jInput = buildLegitimateJudgmentInputFromGovernanceContext(
      {
        delta: ctx.delta,
        evidence: ctx.evidence,
        judgmentAssessment: ctx.judgmentAssessment,
        observerCaptured: ctx.observerCaptured,
        requireJudgmentAssessment: ctx.requireJudgmentAssessment,
        judgmentCycle: ctx.judgmentCycle,
      },
      crkResult.allowed,
    );
    const legitimateJudgment = assessLegitimateJudgment({
      ...crk1jInput,
      corrigibilitySound:
        crk1jInput.corrigibilitySound &&
        !(vetoEscalation?.lineageCorrigibilityFailed ?? false),
      stewardshipAccountable:
        crk1jInput.stewardshipAccountable && !(vetoEscalation?.stewardLineageAtRisk ?? false),
    });
    const crk1jSummary = toLegitimateJudgmentSummary(legitimateJudgment);

    const legitimacy = scoreLegitimacy(crkResult.allowed, adversarial.passed, ctx.evidence.length);

    let decision: RecalibrationDecision = legitimacy.decision;
    let legitimacyBasis = legitimacy.basis;

    if (!crkResult.allowed) {
      decision = "rejected";
      const invDesc = crkResult.violatedInvariants.join(", ");
      legitimacyBasis = `Proposed threshold violates non-derogable invariant(s): ${invDesc}. ${crkResult.reason ?? ""}`.trim();
    } else if (vetoEscalation?.blockThresholdChanges) {
      decision = "rejected";
      legitimacyBasis = `RPA-1 Reality Veto: ${vetoEscalation.reasons.join("; ")}`;
    } else if (!legitimateJudgment.legitimate) {
      decision = recalibrationDecisionFromLegitimateJudgment(legitimateJudgment);
      legitimacyBasis = `CRK-1.J: judgment not legitimate — ${legitimateJudgment.gaps.join("; ")}`;
    } else if (!adversarial.passed) {
      decision = "deferred";
      legitimacyBasis = `Adversarial review incomplete: ${adversarial.notes.join("; ")}`;
    } else if (decision === "approved") {
      legitimacyBasis = `${legitimacy.basis} CRK-1.J satisfied.`;
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
      legitimateJudgment: crk1jSummary,
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
