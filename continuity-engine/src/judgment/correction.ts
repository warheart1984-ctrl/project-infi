import type { JudgmentCapability } from "./capability";
import { clampJudgmentCapability } from "./capability";
import { JUDGMENT_DIMENSIONS } from "./capability";

/** Nudge judgment capability back toward a reference profile. */
export function correctJudgmentToward(
  current: JudgmentCapability,
  reference: JudgmentCapability,
  rate = 0.1,
): JudgmentCapability {
  const corrected = { ...current };
  for (const key of JUDGMENT_DIMENSIONS) {
    corrected[key] = current[key] + rate * (reference[key] - current[key]);
  }
  return clampJudgmentCapability(corrected);
}
