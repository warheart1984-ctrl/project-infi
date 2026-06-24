import type { RecalibrationDecision } from "../css2/types";

export interface LegitimacyScore {
  score: number;
  decision: RecalibrationDecision;
  basis: string;
}

export function scoreLegitimacy(
  crkAllowed: boolean,
  adversarialPassed: boolean,
  evidenceCount: number,
): LegitimacyScore {
  if (!crkAllowed) {
    return {
      score: 0,
      decision: "rejected",
      basis: "CRK-1 invariant violation",
    };
  }
  if (!adversarialPassed) {
    return {
      score: 0.4,
      decision: "deferred",
      basis: "Adversarial review incomplete",
    };
  }
  if (evidenceCount === 0) {
    return {
      score: 0.5,
      decision: "deferred",
      basis: "Evidence documented; awaiting fuller adversarial review",
    };
  }
  return {
    score: 0.85,
    decision: "approved",
    basis: "Evidence documented; adversarial review passed; invariants preserved.",
  };
}
