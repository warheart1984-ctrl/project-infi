/** CRK-1.J.5 — corrigibility classification for judgment cycles. */

export type CorrigibilityStatus = "sound" | "at-risk" | "failed";

export interface JudgmentCycle {
  id: string;
  observerId: string;
  timestamp: string;

  observation: unknown;
  interpretation: unknown;
  valuation: unknown;
  decision: unknown;
  context: unknown;

  outcome: unknown;
  feedback: unknown;
  reflection: unknown;

  relatedThresholdIds?: string[];
  relatedDeltaIds?: string[];
  tags?: string[];

  /** Computed by `assessCorrigibility` / `annotateCorrigibility`. */
  corrigibilityStatus?: CorrigibilityStatus;
}

export interface CorrigibilityAssessment {
  status: CorrigibilityStatus;
  violations: number;
  checks: {
    realityConnectedObservation: boolean;
    challengeableInterpretation: boolean;
    explicitValuation: boolean;
    accountableCommitment: boolean;
    measurableOutcome: boolean;
    behaviorChangingReflection: boolean;
  };
}

function hasRecordField(value: unknown, field: string): boolean {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  const fieldValue = record[field];
  if (fieldValue == null) return false;
  if (Array.isArray(fieldValue)) return fieldValue.length > 0;
  if (typeof fieldValue === "object") return Object.keys(fieldValue).length > 0;
  return true;
}

/** CRK-1.J.5 — Corrigibility Test: can reality still correct this cycle? */
export function assessCorrigibility(c: JudgmentCycle): CorrigibilityAssessment {
  let violations = 0;

  const realityConnectedObservation = c.observation != null;
  const challengeableInterpretation = hasRecordField(c.interpretation, "alternatives");
  const explicitValuation = c.valuation != null;
  const accountableCommitment = hasRecordField(c.decision, "actorId");
  const measurableOutcome = hasRecordField(c.outcome, "metrics");
  const behaviorChangingReflection = hasRecordField(c.reflection, "changes");

  const checks = {
    realityConnectedObservation,
    challengeableInterpretation,
    explicitValuation,
    accountableCommitment,
    measurableOutcome,
    behaviorChangingReflection,
  };

  if (!realityConnectedObservation) violations++;
  if (!challengeableInterpretation) violations++;
  if (!explicitValuation) violations++;
  if (!accountableCommitment) violations++;
  if (!measurableOutcome) violations++;
  if (!behaviorChangingReflection) violations++;

  let status: CorrigibilityStatus;
  if (violations === 0) status = "sound";
  else if (violations <= 2) status = "at-risk";
  else status = "failed";

  return { status, violations, checks };
}

export function annotateCorrigibility(cycle: JudgmentCycle): JudgmentCycle {
  const assessment = assessCorrigibility(cycle);
  return { ...cycle, corrigibilityStatus: assessment.status };
}

/** CRK-1.J.5 — only `sound` cycles satisfy the corrigibility requirement. */
export function isCorrigibilitySound(cycle: JudgmentCycle): boolean {
  return assessCorrigibility(cycle).status === "sound";
}
