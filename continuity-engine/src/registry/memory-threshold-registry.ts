import { createThreshold } from "../css2/threshold";
import type {
  Threshold,
  ThresholdCreateInput,
  ThresholdDelta,
  ThresholdVersion,
} from "../css2/types";
import type { ThresholdQuery, ThresholdRegistry } from "./threshold-registry";

export class InMemoryThresholdRegistry implements ThresholdRegistry {
  private thresholds = new Map<string, Threshold>();
  private history = new Map<string, ThresholdVersion[]>();

  async getById(id: string): Promise<Threshold | null> {
    return this.thresholds.get(id) ?? null;
  }

  async query(q: ThresholdQuery): Promise<Threshold[]> {
    return [...this.thresholds.values()].filter((t) => {
      if (q.domain && t.domain !== q.domain) return false;
      if (q.metric && t.metric !== q.metric) return false;
      if (q.activeOnly && !t.active) return false;
      if (q.context && t.context) {
        for (const [key, val] of Object.entries(q.context)) {
          if (t.context[key] !== val) return false;
        }
      }
      return true;
    });
  }

  async create(input: ThresholdCreateInput): Promise<Threshold> {
    const th = createThreshold(input);
    this.thresholds.set(th.id, th);
    this.appendHistory(th.id, {
      thresholdId: th.id,
      version: 1,
      snapshot: th,
      deltaRationale: "initial",
      createdAt: th.createdAt,
      createdBy: th.createdBy,
    });
    return th;
  }

  async applyDelta(delta: ThresholdDelta, actorId: string): Promise<Threshold> {
    const current = this.thresholds.get(delta.thresholdId);
    if (!current) throw new Error(`Threshold not found: ${delta.thresholdId}`);
    const now = new Date().toISOString();
    const nextVersion = current.version + 1;
    const updated: Threshold = {
      ...current,
      ...delta.after,
      version: nextVersion,
      lastUpdatedAt: now,
      lastUpdatedBy: actorId,
    };
    this.thresholds.set(updated.id, updated);
    this.appendHistory(updated.id, {
      thresholdId: updated.id,
      version: nextVersion,
      snapshot: updated,
      deltaRationale: delta.rationale,
      recalibrationEventId: delta.recalibrationEventId,
      createdAt: now,
      createdBy: actorId,
    });
    return updated;
  }

  async getHistory(thresholdId: string): Promise<ThresholdVersion[]> {
    return (this.history.get(thresholdId) ?? []).sort((a, b) => a.version - b.version);
  }

  private appendHistory(id: string, v: ThresholdVersion): void {
    const arr = this.history.get(id) ?? [];
    arr.push(v);
    this.history.set(id, arr);
  }
}
