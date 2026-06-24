import type { ObserverProfile } from "../css2/types";
import type { JudgmentCapabilityAssessment } from "./judgment-capability";
import { assessObserverJudgment } from "./judgment-capability";
import { JPA1_8_JUDGMENT_FAILURE, OPA1_CONTAINMENT } from "./spec";
import { JUDGMENT_PRESERVING_SYSTEMS } from "./system-mandates";

export interface JPA1ComplianceInput {
  observer?: ObserverProfile;
  judgmentAssessment?: JudgmentCapabilityAssessment;
  systemsPresent?: Array<"JPSS-2" | "CSS-2" | "CRK-1" | "RA-COS-1">;
  evidenceTraceComplete?: boolean;
  thresholdGovernanceActive?: boolean;
  constitutionalInvariantsLoaded?: boolean;
}

export interface JPA1ComplianceResult {
  compliant: boolean;
  jpa1Reference: string;
  opa1Contained: boolean;
  judgmentFailureRisk: boolean;
  failureExplanation?: string;
  checks: Record<string, boolean>;
  gaps: string[];
}

export function assessJPA1Compliance(input: JPA1ComplianceInput): JPA1ComplianceResult {
  const assessment =
    input.judgmentAssessment ??
    (input.observer ? assessObserverJudgment(input.observer) : undefined);

  const systems = new Set(input.systemsPresent ?? ["JPSS-2", "CSS-2", "CRK-1", "RA-COS-1"]);
  const checks: Record<string, boolean> = {};
  const gaps: string[] = [];

  checks["models_judgment_capability"] = assessment !== undefined;
  if (!checks["models_judgment_capability"]) {
    gaps.push("Judgment capability not modeled — provide observer or assessment.");
  }

  checks["observation_prerequisite"] = assessment?.observationSufficient ?? false;
  if (!checks["observation_prerequisite"]) {
    gaps.push("Observation prerequisite weak (perception/interpretation below threshold).");
  }

  checks["judgment_sound"] = assessment?.judgmentSound ?? false;
  if (!checks["judgment_sound"] && assessment) {
    gaps.push(`Judgment composite below threshold; weakest: ${assessment.weakest}.`);
  }

  for (const sys of JUDGMENT_PRESERVING_SYSTEMS) {
    const key = `system_${sys.id}`;
    checks[key] = systems.has(sys.id);
    if (!checks[key]) gaps.push(`Missing judgment-preserving system: ${sys.id}`);
  }

  checks["governs_judgment_training"] = systems.has("JPSS-2");
  checks["governs_threshold_as_judgment"] = input.thresholdGovernanceActive ?? systems.has("CSS-2");
  checks["protects_judgment_conditions"] = input.constitutionalInvariantsLoaded ?? systems.has("CRK-1");
  checks["preserves_judgment_correction_evidence"] =
    input.evidenceTraceComplete ?? systems.has("RA-COS-1");

  const judgmentFailureRisk =
    assessment !== undefined &&
    (!assessment.judgmentSound ||
      (input.observer?.flags.captured ?? false) ||
      (input.observer?.driftScore ?? 0) > 0.85);

  const compliant =
    checks["models_judgment_capability"] &&
    checks["observation_prerequisite"] &&
    checks["judgment_sound"] &&
    checks["governs_judgment_training"] &&
    checks["governs_threshold_as_judgment"] &&
    checks["protects_judgment_conditions"] &&
    checks["preserves_judgment_correction_evidence"] &&
    !judgmentFailureRisk;

  return {
    compliant,
    jpa1Reference: "JPA-1",
    opa1Contained: true,
    judgmentFailureRisk,
    failureExplanation: judgmentFailureRisk ? JPA1_8_JUDGMENT_FAILURE : undefined,
    checks,
    gaps,
  };
}

export function opa1ImpliedByJpa1(): string {
  return OPA1_CONTAINMENT;
}
