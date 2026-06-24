import type { JudgmentCapabilityAssessment } from "../jpa1/judgment-capability";
import type { CorrigibilityStatus, JudgmentCycle } from "../judgment/cycle";
import { assessCorrigibility, isCorrigibilitySound } from "../judgment/cycle";

/** CRK-1.J — legitimate judgment constitutional requirements. */
export const CRK1_J_REQUIREMENTS = {
  observationIntegrity: "OPA-1 — reality-responsive observation",
  evidenceTraceability: "RA-COS-1 — reconstructable evidence trail",
  invariantCompliance: "CRK-1 core — non-derogable invariants",
  stewardshipAccountability: "Future stewards can critique/revise without identity loss",
  judgmentCapabilityPreservation: "JPA-1 — sound judgment capability preserved",
  corrigibility: "CRK-1.J.5 — reality can still correct the judgment cycle",
} as const;

export type CRK1JRequirementKey = keyof typeof CRK1_J_REQUIREMENTS;

export interface LegitimateJudgmentInput {
  /** OPA-1 — observation integrity satisfied. */
  observationIntegrity: boolean;
  /** RA-COS-1 — evidence trail is reconstructable. */
  evidenceTraceable: boolean;
  /** CRK-1 core — no invariant violations. */
  invariantCompliant: boolean;
  /** Judgment can be revised by future stewards. */
  stewardshipAccountable: boolean;
  /** JPA-1 — judgment capability not degraded. */
  judgmentCapabilityPreserved: boolean;
  /** CRK-1.J.5 — corrigibility sound (reality-correctable cycle). */
  corrigibilitySound: boolean;
  /** Optional assessment for detailed gaps. */
  judgmentAssessment?: JudgmentCapabilityAssessment;
  /** Optional cycle for corrigibility detail in gaps. */
  corrigibilityStatus?: CorrigibilityStatus;
}

export interface LegitimateJudgmentResult {
  legitimate: boolean;
  category: "CRK-1.J";
  satisfiedRequirements: CRK1JRequirementKey[];
  failedRequirements: CRK1JRequirementKey[];
  constitutionalTriad: {
    opa1: "observation inputs";
    jpa1: "judgment capability";
    crk1j: "judgment legitimacy";
  };
  gaps: string[];
}

const REQUIREMENT_CHECKS: Array<{
  key: CRK1JRequirementKey;
  field: keyof LegitimateJudgmentInput;
  gapMessage: string;
}> = [
  {
    key: "observationIntegrity",
    field: "observationIntegrity",
    gapMessage: "Observation integrity not satisfied (OPA-1).",
  },
  {
    key: "evidenceTraceability",
    field: "evidenceTraceable",
    gapMessage: "Evidence trail not reconstructable (RA-COS-1).",
  },
  {
    key: "invariantCompliance",
    field: "invariantCompliant",
    gapMessage: "Non-derogable invariant violation (CRK-1).",
  },
  {
    key: "stewardshipAccountability",
    field: "stewardshipAccountable",
    gapMessage: "Stewardship accountability not established.",
  },
  {
    key: "judgmentCapabilityPreservation",
    field: "judgmentCapabilityPreserved",
    gapMessage: "Judgment capability would be degraded (JPA-1).",
  },
  {
    key: "corrigibility",
    field: "corrigibilitySound",
    gapMessage: "Corrigibility requirement not satisfied (CRK-1.J.5).",
  },
];

/**
 * CRK-1.J.3 — No threshold adoption, Δ-Threshold, or recalibration is legitimate
 * unless all five requirements are satisfied.
 */
export function assessLegitimateJudgment(
  input: LegitimateJudgmentInput,
): LegitimateJudgmentResult {
  const satisfiedRequirements: CRK1JRequirementKey[] = [];
  const failedRequirements: CRK1JRequirementKey[] = [];
  const gaps: string[] = [];

  for (const check of REQUIREMENT_CHECKS) {
    if (input[check.field]) {
      satisfiedRequirements.push(check.key);
    } else {
      failedRequirements.push(check.key);
      gaps.push(check.gapMessage);
    }
  }

  if (input.judgmentAssessment && !input.judgmentAssessment.judgmentSound) {
    if (!gaps.some((g) => g.includes("JPA-1"))) {
      gaps.push(
        `Judgment composite weak (weakest: ${input.judgmentAssessment.weakest}).`,
      );
    }
  }

  if (!input.corrigibilitySound && input.corrigibilityStatus) {
    gaps.push(`Corrigibility status: ${input.corrigibilityStatus}.`);
  }

  return {
    legitimate: failedRequirements.length === 0,
    category: "CRK-1.J",
    satisfiedRequirements,
    failedRequirements,
    constitutionalTriad: {
      opa1: "observation inputs",
      jpa1: "judgment capability",
      crk1j: "judgment legitimacy",
    },
    gaps,
  };
}

/** Build legitimacy input from common governance context. */
export function buildLegitimateJudgmentInput(params: {
  crkAllowed: boolean;
  evidenceCount: number;
  judgmentAssessment?: JudgmentCapabilityAssessment;
  observerCaptured?: boolean;
  identityIntentPreserved?: boolean;
  judgmentCycle?: JudgmentCycle;
  corrigibilitySound?: boolean;
}): LegitimateJudgmentInput {
  const assessment = params.judgmentAssessment;
  const corrigibilityStatus = params.judgmentCycle
    ? assessCorrigibility(params.judgmentCycle).status
    : undefined;
  const corrigibilitySound =
    params.corrigibilitySound ??
    (params.judgmentCycle ? isCorrigibilitySound(params.judgmentCycle) : true);

  return {
    observationIntegrity: assessment?.observationSufficient ?? false,
    evidenceTraceable: params.evidenceCount > 0,
    invariantCompliant: params.crkAllowed,
    stewardshipAccountable:
      (params.identityIntentPreserved ?? true) && !(params.observerCaptured ?? false),
    judgmentCapabilityPreserved: assessment?.judgmentSound ?? false,
    corrigibilitySound,
    judgmentAssessment: assessment,
    corrigibilityStatus,
  };
}

/** Detect core identity/mission intent change in a Δ-threshold proposal. */
export function coreIdentityIntentChanged(delta: {
  before: { intent: string; domain: string };
  after: { intent?: string };
}): boolean {
  const afterIntent = delta.after.intent ?? delta.before.intent;
  const coreIntent =
    delta.before.intent.includes("mission") ||
    delta.before.intent.includes("identity") ||
    delta.before.domain.includes("Core");
  return coreIntent && afterIntent !== delta.before.intent;
}

/** Governance bridge — CRK-1.J input from Δ-threshold evaluation context. */
export function buildLegitimateJudgmentInputFromGovernanceContext(
  ctx: {
    delta: { before: { intent: string; domain: string }; after: { intent?: string } };
    evidence: unknown[];
    judgmentAssessment?: JudgmentCapabilityAssessment;
    observerCaptured?: boolean;
    requireJudgmentAssessment?: boolean;
    judgmentCycle?: JudgmentCycle;
  },
  crkAllowed: boolean,
): LegitimateJudgmentInput {
  const identityIntentPreserved = !coreIdentityIntentChanged(ctx.delta);
  const base = buildLegitimateJudgmentInput({
    crkAllowed,
    evidenceCount: ctx.evidence.length,
    judgmentAssessment: ctx.judgmentAssessment,
    observerCaptured: ctx.observerCaptured,
    identityIntentPreserved,
    judgmentCycle: ctx.judgmentCycle,
  });

  if (ctx.requireJudgmentAssessment && !ctx.judgmentAssessment) {
    return {
      ...base,
      observationIntegrity: false,
      judgmentCapabilityPreserved: false,
      corrigibilitySound: ctx.judgmentCycle ? base.corrigibilitySound : false,
    };
  }

  if (!ctx.judgmentAssessment) {
    return {
      ...base,
      observationIntegrity: ctx.evidence.length > 0,
      judgmentCapabilityPreserved: crkAllowed && identityIntentPreserved,
      corrigibilitySound: ctx.judgmentCycle ? base.corrigibilitySound : true,
    };
  }

  return base;
}

/** Map CRK-1.J failure to recalibration decision. */
export function recalibrationDecisionFromLegitimateJudgment(
  result: LegitimateJudgmentResult,
): "approved" | "rejected" | "deferred" {
  if (result.legitimate) return "approved";
  const hardReject = result.failedRequirements.some((r) =>
    ["invariantCompliance", "stewardshipAccountability", "corrigibility"].includes(r),
  );
  if (hardReject) return "rejected";
  return "deferred";
}
