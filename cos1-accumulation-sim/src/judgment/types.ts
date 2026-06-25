/** Payload for one phase of a judgment cycle (ledger v2) */
export interface CyclePayload extends Record<string, unknown> {
  summary?: string;
  eventIds?: string[];
  timestamp?: string;
}

/** Continuity Ledger v2 root artifact — completed judgment cycle */
export interface JudgmentCycle {
  id: string;
  observerId: string;
  timestamp: string;

  observation: CyclePayload;
  interpretation: CyclePayload;
  valuation: CyclePayload;
  decision: CyclePayload;
  context: CyclePayload;

  outcome: CyclePayload;
  feedback: CyclePayload;
  reflection: CyclePayload;

  relatedThresholdIds?: string[];
  relatedDeltaIds?: string[];
  tags?: string[];
}

/** In-progress cycle during event assembly (not yet in ledger) */
export interface JudgmentCycleDraft extends JudgmentCycle {
  status: "OPEN" | "COMPLETE";
  startedAt: string;
  /** Lineage links accumulated during assembly */
  buildsOn: string[];
}

/** Analytics layer — hypothesis inferred from cycles, not ground truth */
export interface JudgmentCapabilityProfile {
  perception: number;
  interpretation: number;
  valuation: number;
  deliberation: number;
  commitment: number;
  reflection: number;
  evidenceCycles: string[];
  score: number;
}

export type JudgmentCapabilityVector = Pick<
  JudgmentCapabilityProfile,
  "perception" | "interpretation" | "valuation" | "deliberation" | "commitment" | "reflection"
>;

export interface JudgmentEvaluation {
  score: number;
  dimensions: JudgmentCapabilityVector;
  evidenceCycleCount: number;
  isHypothesis: true;
}

export type CycleLike = JudgmentCycle | JudgmentCycleDraft;
