import type { JudgmentCapabilityProfile, JudgmentCapabilityVector } from "../types.js";

function vectorDistance(a: JudgmentCapabilityVector, b: JudgmentCapabilityVector): number {
  const keys = [
    "perception",
    "interpretation",
    "valuation",
    "deliberation",
    "commitment",
    "reflection",
  ] as const;
  let sum = 0;
  for (const k of keys) {
    sum += Math.abs(a[k] - b[k]);
  }
  return sum / keys.length;
}

/** Drift between two cycle-derived profiles (0 = stable, 1 = maximal drift) */
export function computeJudgmentDriftFromProfiles(
  previous: JudgmentCapabilityProfile,
  current: JudgmentCapabilityProfile,
): number {
  if (previous.evidenceCycles.length === 0 || current.evidenceCycles.length === 0) {
    return 0;
  }
  return vectorDistance(previous, current);
}
