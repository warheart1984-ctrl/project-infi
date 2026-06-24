import type { ObserverProfile, ObserverStage } from "../css2/types";

export type CurriculumModuleId =
  | "perception_101"
  | "interpretation_101"
  | "hypothesis_101"
  | "judgment_101"
  | "stewardship_101";

export interface CurriculumModule {
  id: CurriculumModuleId;
  name: string;
  description: string;
  targetStages: ObserverStage[];
  effects: Partial<ObserverProfile["capabilities"]>;
}

export const JPSS2_CURRICULUM: CurriculumModule[] = [
  {
    id: "perception_101",
    name: "Perceptual Discipline",
    description: "Training to notice anomalies, contradictions, and absences.",
    targetStages: ["person", "observer"],
    effects: { perception: 0.1 },
  },
  {
    id: "interpretation_101",
    name: "Interpretive Discipline",
    description: "Turning raw anomalies into coherent ObservationPatterns.",
    targetStages: ["observer", "senior_observer"],
    effects: { interpretation: 0.1 },
  },
  {
    id: "hypothesis_101",
    name: "Hypothesis Discipline",
    description: "Formulating ProtoThresholds that can be tested.",
    targetStages: ["observer", "senior_observer"],
    effects: { hypothesis: 0.1 },
  },
  {
    id: "judgment_101",
    name: "Judgment Discipline",
    description: "Deciding which ProtoThresholds should become Thresholds.",
    targetStages: ["senior_observer", "steward"],
    effects: { judgment: 0.1 },
  },
  {
    id: "stewardship_101",
    name: "Stewardship Discipline",
    description: "Detecting when one's own interpretations are drifting.",
    targetStages: ["steward"],
    effects: { stewardship: 0.1 },
  },
];
