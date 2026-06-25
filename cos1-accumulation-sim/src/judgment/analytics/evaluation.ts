import type { JudgmentCapabilityProfile, JudgmentEvaluation, CycleLike } from "../types.js";
import { inferCapabilityProfile } from "./capability.js";

/** Evaluate judgment from cycle evidence — score is always a hypothesis */
export function evaluateJudgmentFromCycles(
  cycles: CycleLike[],
  observerId: string,
): JudgmentEvaluation {
  const profile = inferCapabilityProfile(cycles, observerId, { minComplete: 1 });
  return {
    score: profile.score,
    dimensions: {
      perception: profile.perception,
      interpretation: profile.interpretation,
      valuation: profile.valuation,
      deliberation: profile.deliberation,
      commitment: profile.commitment,
      reflection: profile.reflection,
    },
    evidenceCycleCount: profile.evidenceCycles.length,
    isHypothesis: true,
  };
}

export function evaluateJudgmentFromProfile(profile: JudgmentCapabilityProfile): JudgmentEvaluation {
  return {
    score: profile.score,
    dimensions: {
      perception: profile.perception,
      interpretation: profile.interpretation,
      valuation: profile.valuation,
      deliberation: profile.deliberation,
      commitment: profile.commitment,
      reflection: profile.reflection,
    },
    evidenceCycleCount: profile.evidenceCycles.length,
    isHypothesis: true,
  };
}
