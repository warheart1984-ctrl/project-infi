/** JPA-1 — Judgment capability as a first-class runtime object. */

export interface JudgmentCapability {
  perception: number;
  interpretation: number;
  valuation: number;
  deliberation: number;
  commitment: number;
  reflection: number;
}

export type JudgmentDimension = keyof JudgmentCapability;

export const JUDGMENT_DIMENSIONS: readonly JudgmentDimension[] = [
  "perception",
  "interpretation",
  "valuation",
  "deliberation",
  "commitment",
  "reflection",
] as const;

export function emptyJudgmentCapability(): JudgmentCapability {
  return {
    perception: 0,
    interpretation: 0,
    valuation: 0,
    deliberation: 0,
    commitment: 0,
    reflection: 0,
  };
}

export function clampJudgmentCapability(cap: JudgmentCapability): JudgmentCapability {
  const clamp = (n: number) => Math.min(1, Math.max(0, n));
  return {
    perception: clamp(cap.perception),
    interpretation: clamp(cap.interpretation),
    valuation: clamp(cap.valuation),
    deliberation: clamp(cap.deliberation),
    commitment: clamp(cap.commitment),
    reflection: clamp(cap.reflection),
  };
}
