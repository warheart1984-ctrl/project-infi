import type { JudgmentCycle } from "../judgment/types.js";
import type { RecalibrationView, ThresholdView } from "./types.js";

function decisionType(cycle: JudgmentCycle): string | undefined {
  const t = cycle.decision.type;
  return typeof t === "string" ? t : undefined;
}

/** Thresholds are projections over cycles — not stored as canonical objects */
export function deriveThresholdViews(cycles: JudgmentCycle[]): ThresholdView[] {
  const byId = new Map<string, ThresholdView>();

  for (const cycle of cycles) {
    if (decisionType(cycle) !== "threshold_adoption") continue;

    const thresholdId = String(cycle.decision.thresholdId ?? cycle.id);
    const existing = byId.get(thresholdId);

    if (existing) {
      existing.supportingCycleIds.push(cycle.id);
      if (cycle.timestamp > existing.lastUpdatedAt) {
        existing.lastUpdatedAt = cycle.timestamp;
        existing.value = Number(cycle.decision.value ?? existing.value);
      }
      continue;
    }

    byId.set(thresholdId, {
      id: thresholdId,
      domain: String(cycle.decision.domain ?? cycle.context.domain ?? "unknown"),
      metric: String(cycle.decision.metric ?? "unspecified"),
      comparator: String(cycle.decision.comparator ?? ">="),
      value: Number(cycle.decision.value ?? 0),
      supportingCycleIds: [cycle.id],
      lastUpdatedAt: cycle.timestamp,
      createdByObserverId: cycle.observerId,
    });
  }

  return [...byId.values()];
}

/** Δ-Threshold recalibrations are specialized judgment cycles */
export function deriveRecalibrationViews(
  cycles: JudgmentCycle[],
  thresholdId?: string,
): RecalibrationView[] {
  const views: RecalibrationView[] = [];

  for (const cycle of cycles) {
    if (decisionType(cycle) !== "threshold_recalibration") continue;

    const tid = String(cycle.decision.thresholdId ?? "");
    if (thresholdId && tid !== thresholdId) continue;

    views.push({
      id: `RC_${cycle.id}`,
      thresholdId: tid,
      fromValue: Number(cycle.decision.fromValue ?? 0),
      toValue: Number(cycle.decision.toValue ?? cycle.decision.value ?? 0),
      cycleId: cycle.id,
      createdAt: cycle.timestamp,
      createdByObserverId: cycle.observerId,
    });
  }

  return views;
}
