import type { ThresholdVersion } from "../css2/types";

export interface ThresholdChartPoint {
  version: number;
  timestamp: string;
  value: unknown;
  rationale: string;
  eventId: string | null;
}

export interface ThresholdChartSpec {
  type: "line-chart";
  title: string;
  xField: "timestamp";
  yField: "value";
  points: ThresholdChartPoint[];
}

export function generateThresholdChartSpec(history: ThresholdVersion[]): ThresholdChartSpec {
  return {
    type: "line-chart",
    title: `Threshold Lineage: ${history[0]?.thresholdId ?? "unknown"}`,
    xField: "timestamp",
    yField: "value",
    points: history.map((v) => ({
      version: v.version,
      timestamp: v.snapshot.lastUpdatedAt,
      value: v.snapshot.value,
      rationale: v.deltaRationale,
      eventId: v.recalibrationEventId ?? null,
    })),
  };
}

/** @deprecated Use generateThresholdChartSpec */
export const emitThresholdChartSpec = generateThresholdChartSpec;
