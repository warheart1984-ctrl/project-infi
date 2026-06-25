import type { AccumulationOrigin, AccumulationType } from "./domain.js";
export type {
  GameEvent,
  GameEventType,
  AccumulationTag,
  WorldChangeProposal,
  WorldLayer,
} from "./domain.js";

export interface ContinuityHealthResponse {
  accumulation: {
    PLA: { count: number; actors: number };
    LA: { count: number; actors: number };
    SA: { count: number; actors: number };
  };
  mat3: boolean;
  plt1: boolean;
  interpretation: string;
  reconstructability: {
    reconstructionCost: number;
    reconstructionThreshold: number;
    k4Satisfied: boolean;
  };
  drift: { aggregatePSD: number } | null;
  couplingStrength: number;
  epistemic: import("./domain.js").EpistemicMetrics;
  pla: {
    clustering: number;
    crossDomainRecurrence: number;
    validationSurvival: number;
    instrumentality: number;
  };
}

export interface WorldChangeHypothesis {
  expectedEffects: string[];
  metrics: string[];
  validationWindowDays: number;
}

export interface WorldEvent {
  id: string;
  actorId: string;
  timestamp: string;
  type: import("./domain.js").GameEventType;
  payload: Record<string, unknown>;
}

export interface WorldChange {
  id: string;
  description: string;
  origin: AccumulationOrigin;
  accumulationType: AccumulationType;
  proposedBy: string;
  affectsSystems: string[];
  status: "PROVISIONAL" | "VALIDATED" | "REJECTED" | "ROLLED_BACK";
  acceptedAt: string | null;
  validatedAt: string | null;
  hypothesis?: WorldChangeHypothesis;
}

export interface PlayerProfile {
  id: string;
  name: string;
  plaCount: number;
  laCount: number;
  saCount: number;
  reconstructabilityScore: number;
  stewardshipScore: number;
  roles: string[];
}

export interface Faction {
  id: string;
  name: string;
  ideology: string;
  members: string[];
  influenceScore: number;
}
