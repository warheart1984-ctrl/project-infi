import type { ObserverProfile } from "../css2/types";
import type { JudgmentCapabilityDimension } from "./spec";

/** JPA-1 §4 — composite judgment capability vector (0–1 per dimension). */
export interface JudgmentCapabilityVector {
  perception: number;
  interpretation: number;
  valuation: number;
  deliberation: number;
  commitment: number;
  reflection: number;
}

export interface JudgmentCapabilityAssessment {
  vector: JudgmentCapabilityVector;
  compositeScore: number;
  weakest: JudgmentCapabilityDimension;
  observationSufficient: boolean;
  judgmentSound: boolean;
  notes: string[];
}

const MIN_OBSERVATION = 0.35;
const MIN_JUDGMENT_COMPOSITE = 0.45;
const MIN_REFLECTION = 0.3;

/** Map legacy ObserverProfile capabilities to JPA-1 six-dimension vector. */
export function observerToJudgmentVector(observer: ObserverProfile): JudgmentCapabilityVector {
  const c = observer.capabilities;
  return {
    perception: c.perception,
    interpretation: c.interpretation,
    valuation: clamp01(c.hypothesis * 0.6 + c.judgment * 0.4),
    deliberation: c.judgment,
    commitment: clamp01(c.judgment * 0.7 + c.stewardship * 0.3),
    reflection: c.stewardship,
  };
}

export function assessJudgmentCapability(
  vector: JudgmentCapabilityVector,
): JudgmentCapabilityAssessment {
  const values = Object.values(vector);
  const compositeScore = values.reduce((s, v) => s + v, 0) / values.length;
  const weakest = (Object.entries(vector) as [JudgmentCapabilityDimension, number][]).reduce(
    (min, [k, v]) => (v < min[1] ? [k, v] : min),
    ["perception", 1] as [JudgmentCapabilityDimension, number],
  )[0];

  const notes: string[] = [];
  if (vector.perception < MIN_OBSERVATION) notes.push("Weak perception — observation prerequisite at risk.");
  if (vector.interpretation < MIN_OBSERVATION) notes.push("Weak interpretation — patterns may not cohere.");
  if (vector.reflection < MIN_REFLECTION) notes.push("Weak reflection — self-correction capacity degraded.");
  if (vector.valuation < 0.3) notes.push("Weak valuation — priorities may not align with purpose.");
  if (vector.deliberation < 0.3) notes.push("Weak deliberation — trade-offs under-weighted.");
  if (vector.commitment < 0.3) notes.push("Weak commitment — decisions may not land under uncertainty.");

  const observationSufficient =
    vector.perception >= MIN_OBSERVATION && vector.interpretation >= MIN_OBSERVATION;
  const judgmentSound = observationSufficient && compositeScore >= MIN_JUDGMENT_COMPOSITE;

  return {
    vector,
    compositeScore,
    weakest,
    observationSufficient,
    judgmentSound,
    notes,
  };
}

export function assessObserverJudgment(observer: ObserverProfile): JudgmentCapabilityAssessment {
  return assessJudgmentCapability(observerToJudgmentVector(observer));
}

function clamp01(n: number): number {
  return Math.min(1, Math.max(0, n));
}
