import type {
  Threshold,
  ThresholdCreateInput,
  ThresholdDelta,
  ThresholdVersion,
} from "../css2/types";
import type { ThresholdQuery, ThresholdRegistry } from "./threshold-registry";

/** DB-backed registry — implement with your Pool/Client. */
export abstract class DbThresholdRegistry implements ThresholdRegistry {
  abstract getById(id: string): Promise<Threshold | null>;
  abstract query(q: ThresholdQuery): Promise<Threshold[]>;
  abstract create(input: ThresholdCreateInput): Promise<Threshold>;
  abstract applyDelta(delta: ThresholdDelta, actorId: string): Promise<Threshold>;
  abstract getHistory(thresholdId: string): Promise<ThresholdVersion[]>;
}
