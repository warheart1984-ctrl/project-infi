import type {
  Threshold,
  ThresholdCreateInput,
  ThresholdDelta,
  ThresholdVersion,
} from "../css2/types";

export interface ThresholdQuery {
  domain?: string;
  metric?: string;
  context?: Record<string, unknown>;
  activeOnly?: boolean;
}

export interface ThresholdRegistry {
  getById(id: string): Promise<Threshold | null>;
  query(q: ThresholdQuery): Promise<Threshold[]>;
  create(input: ThresholdCreateInput): Promise<Threshold>;
  applyDelta(delta: ThresholdDelta, actorId: string): Promise<Threshold>;
  getHistory(thresholdId: string): Promise<ThresholdVersion[]>;
}

export interface ThresholdPersistenceSnapshot {
  thresholds: Threshold[];
  history: Record<string, ThresholdVersion[]>;
}
