import type { JudgmentCapability } from "./capability";
import { JUDGMENT_DIMENSIONS } from "./capability";

export interface JudgmentEvaluation {
  score: number;
  weaknesses: string[];
  /** Dimensions below the weakness threshold (default 0.4). */
  weakDimensions: (keyof JudgmentCapability)[];
}

const WEAKNESS_THRESHOLD = 0.4;

export function evaluateJudgment(
  cap: JudgmentCapability,
  weaknessThreshold = WEAKNESS_THRESHOLD,
): JudgmentEvaluation {
  const values = JUDGMENT_DIMENSIONS.map((k) => cap[k]);
  const score = values.reduce((a, b) => a + b, 0) / values.length;

  const weaknesses: string[] = [];
  const weakDimensions: (keyof JudgmentCapability)[] = [];

  if (cap.perception < weaknessThreshold) {
    weaknesses.push("Weak perception");
    weakDimensions.push("perception");
  }
  if (cap.interpretation < weaknessThreshold) {
    weaknesses.push("Weak interpretation");
    weakDimensions.push("interpretation");
  }
  if (cap.valuation < weaknessThreshold) {
    weaknesses.push("Weak valuation");
    weakDimensions.push("valuation");
  }
  if (cap.deliberation < weaknessThreshold) {
    weaknesses.push("Weak deliberation");
    weakDimensions.push("deliberation");
  }
  if (cap.commitment < weaknessThreshold) {
    weaknesses.push("Weak commitment");
    weakDimensions.push("commitment");
  }
  if (cap.reflection < weaknessThreshold) {
    weaknesses.push("Weak reflection");
    weakDimensions.push("reflection");
  }

  return { score, weaknesses, weakDimensions };
}

/** JPA-1.8 — judgment failure when composite score collapses or reflection is absent. */
export function isJudgmentFailure(
  cap: JudgmentCapability,
  options: { scoreFloor?: number; requireReflection?: boolean } = {},
): boolean {
  const scoreFloor = options.scoreFloor ?? 0.35;
  const evaluation = evaluateJudgment(cap);
  if (evaluation.score < scoreFloor) return true;
  if (options.requireReflection !== false && cap.reflection < 0.25) return true;
  return false;
}
