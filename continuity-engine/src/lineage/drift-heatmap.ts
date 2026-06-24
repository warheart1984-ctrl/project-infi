import type { ThresholdVersion } from "../css2/types";

export interface DriftHeatmapCell {
  thresholdId: string;
  version: number;
  driftMagnitude: number;
  timestamp: string;
}

export interface DriftHeatmapSpec {
  type: "heatmap";
  title: string;
  cells: DriftHeatmapCell[];
}

export function generateDriftHeatmap(history: ThresholdVersion[]): DriftHeatmapSpec {
  const cells: DriftHeatmapCell[] = [];
  for (let i = 1; i < history.length; i++) {
    const prev = history[i - 1]!;
    const curr = history[i]!;
    const prevVal = typeof prev.snapshot.value === "number" ? prev.snapshot.value : 0;
    const currVal = typeof curr.snapshot.value === "number" ? curr.snapshot.value : 0;
    const magnitude = prevVal === 0 ? Math.abs(currVal) : Math.abs((currVal - prevVal) / prevVal);
    cells.push({
      thresholdId: curr.thresholdId,
      version: curr.version,
      driftMagnitude: magnitude,
      timestamp: curr.snapshot.lastUpdatedAt,
    });
  }
  return {
    type: "heatmap",
    title: `Drift Heatmap: ${history[0]?.thresholdId ?? "unknown"}`,
    cells,
  };
}
