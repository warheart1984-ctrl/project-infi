import type { ObserverProfile, ObserverStage } from "../css2/types";
import type { JudgmentDimension } from "../judgment/capability";

export type JudgmentCurriculumModuleId =
  | "perception_201"
  | "interpretation_202"
  | "valuation_203"
  | "deliberation_204"
  | "commitment_205"
  | "reflection_206";

export interface JudgmentCurriculumModule {
  id: JudgmentCurriculumModuleId;
  name: string;
  description: string;
  /** Primary JPA-1 judgment dimension trained by this module. */
  dimension: JudgmentDimension;
  targetStages: ObserverStage[];
  /** Effect on observer capabilities (maps to judgment via JPSS-2.J pipeline). */
  effects: Partial<ObserverProfile["capabilities"]>;
}

/** JPSS-2.J.1 — six-dimension judgment capability curriculum. */
export const JPSS2_JUDGMENT_CURRICULUM: readonly JudgmentCurriculumModule[] = [
  {
    id: "perception_201",
    name: "Perception 201 — Anomaly Literacy",
    description: "Noticing anomalies, contradictions, and absences.",
    dimension: "perception",
    targetStages: ["person", "observer"],
    effects: { perception: 0.1 },
  },
  {
    id: "interpretation_202",
    name: "Interpretation 202 — Pattern Formation",
    description: "Forming coherent patterns from observations.",
    dimension: "interpretation",
    targetStages: ["observer", "senior_observer"],
    effects: { interpretation: 0.1 },
  },
  {
    id: "valuation_203",
    name: "Valuation 203 — Prioritization and Moral Weight",
    description: "Deciding what matters and assigning priority.",
    dimension: "valuation",
    targetStages: ["observer", "senior_observer"],
    effects: { hypothesis: 0.06, judgment: 0.04 },
  },
  {
    id: "deliberation_204",
    name: "Deliberation 204 — Trade-off Reasoning",
    description: "Weighing trade-offs and risks under uncertainty.",
    dimension: "deliberation",
    targetStages: ["senior_observer", "steward"],
    effects: { hypothesis: 0.08, judgment: 0.02 },
  },
  {
    id: "commitment_205",
    name: "Commitment 205 — Threshold Formation",
    description: "Selecting actions and adopting thresholds under uncertainty.",
    dimension: "commitment",
    targetStages: ["senior_observer", "steward"],
    effects: { judgment: 0.1 },
  },
  {
    id: "reflection_206",
    name: "Reflection 206 — Recalibration Discipline",
    description: "Revising judgments in light of new evidence.",
    dimension: "reflection",
    targetStages: ["steward"],
    effects: { stewardship: 0.1 },
  },
];

/** JPSS-2.J.2 — stage → primary judgment capabilities. */
export const STAGE_JUDGMENT_FOCUS: Record<ObserverStage, JudgmentDimension[]> = {
  person: ["perception"],
  observer: ["perception", "interpretation"],
  senior_observer: ["valuation", "deliberation"],
  steward: ["deliberation", "commitment", "reflection"],
};

export function applyJudgmentCurriculumModule(
  observer: ObserverProfile,
  module: JudgmentCurriculumModule,
): ObserverProfile {
  if (!module.targetStages.includes(observer.stage)) {
    return observer;
  }
  const caps = { ...observer.capabilities };
  for (const [k, v] of Object.entries(module.effects)) {
    const key = k as keyof typeof caps;
    caps[key] = Math.min(1, caps[key] + (v ?? 0));
  }
  return { ...observer, capabilities: caps };
}

export function developJudgmentCapabilities(
  observer: ObserverProfile,
  moduleIds: JudgmentCurriculumModuleId[] = JPSS2_JUDGMENT_CURRICULUM.map((m) => m.id),
): ObserverProfile {
  let current = observer;
  for (const modId of moduleIds) {
    const mod = JPSS2_JUDGMENT_CURRICULUM.find((m) => m.id === modId);
    if (mod) {
      current = applyJudgmentCurriculumModule(current, mod);
    }
  }
  return current;
}
