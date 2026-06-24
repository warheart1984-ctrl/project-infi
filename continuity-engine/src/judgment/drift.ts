import type { JudgmentCapability } from "./capability";
import { JUDGMENT_DIMENSIONS } from "./capability";

/** Judgment drift: divergence between past and present judgment patterns. */
export function computeJudgmentDrift(
  previous: JudgmentCapability,
  current: JudgmentCapability,
): number {
  const diffs = JUDGMENT_DIMENSIONS.map((key) =>
    Math.abs(previous[key] - current[key]),
  );
  const avg = diffs.reduce((a, b) => a + b, 0) / diffs.length;
  return Math.min(1, avg);
}
