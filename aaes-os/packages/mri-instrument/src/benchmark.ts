import type { MRIComparison, MRIResult } from './index.js';

/** Public-facing scores on 0–100 scale (MRI Operator v0.2). */
export type PublicDimensionScores = {
  continuity: number;
  governance: number;
  memory: number;
  coordination: number;
  confidence: number;
};

export type PublicStateVector = PublicDimensionScores;

export type BenchmarkSnapshot = {
  industryAverage: PublicDimensionScores;
  topQuartile: PublicDimensionScores;
  previousMeasurement: PublicDimensionScores;
};

export type BenchmarkDelta = {
  dimension: keyof PublicDimensionScores;
  vsPrevious: number;
  vsIndustry: number;
  vsTopQuartile: number;
};

export type BenchmarkSummary = {
  deltas: BenchmarkDelta[];
  narrative: string;
};

export type BenchmarkBarMarkers = {
  current: number;
  previous: number;
  industry: number;
  topQuartile: number;
};

function clampScore(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

/** Map internal MRI result to public 0–100 scores; coordination from state.X. */
export function publicScoresFromMRIResult(result: MRIResult): PublicStateVector {
  return {
    continuity: clampScore(result.scores.continuity),
    governance: clampScore(result.scores.governance),
    memory: clampScore(result.scores.memory),
    coordination: clampScore(result.state.X),
    confidence: clampScore(result.scores.confidence * 100),
  };
}

/** Before/after public scores from a comparison run. */
export function publicScoresFromComparison(comparison: MRIComparison): {
  before: PublicStateVector;
  after: PublicStateVector;
} {
  return {
    before: publicScoresFromMRIResult(comparison.before),
    after: publicScoresFromMRIResult(comparison.after),
  };
}

/** Normalized delta in ~[-1, 1] per dimension (score-scale change / 100). */
export function computePublicDeltaState(
  before: PublicStateVector,
  after: PublicStateVector,
): PublicDimensionScores {
  const keys = ['continuity', 'governance', 'memory', 'coordination', 'confidence'] as const;
  const out = {} as PublicDimensionScores;
  for (const key of keys) {
    out[key] = Number(((after[key] - before[key]) / 100).toFixed(4));
  }
  return out;
}

export function computeBenchmarkDeltas(
  current: PublicStateVector,
  benchmarks: BenchmarkSnapshot,
): BenchmarkDelta[] {
  const keys = ['continuity', 'governance', 'memory', 'coordination', 'confidence'] as const;
  return keys.map((dimension) => ({
    dimension,
    vsPrevious: current[dimension] - benchmarks.previousMeasurement[dimension],
    vsIndustry: current[dimension] - benchmarks.industryAverage[dimension],
    vsTopQuartile: current[dimension] - benchmarks.topQuartile[dimension],
  }));
}

/** Human-readable benchmark summary for the Operator UI. */
export function summarizeBenchmarks(
  current: PublicStateVector,
  benchmarks: BenchmarkSnapshot,
): string {
  const deltas = computeBenchmarkDeltas(current, benchmarks);
  const continuity = deltas.find((d) => d.dimension === 'continuity');
  const governance = deltas.find((d) => d.dimension === 'governance');
  const memory = deltas.find((d) => d.dimension === 'memory');

  const avgVsIndustry =
    deltas.reduce((sum, d) => sum + d.vsIndustry, 0) / deltas.length;
  const avgVsTop =
    deltas.reduce((sum, d) => sum + d.vsTopQuartile, 0) / deltas.length;
  const avgVsPrev =
    deltas.reduce((sum, d) => sum + d.vsPrevious, 0) / deltas.length;

  const fmt = (n: number) => (n >= 0 ? `+${Math.round(n)}` : String(Math.round(n)));

  const parts = [
    `${fmt(avgVsIndustry)} vs industry (avg)`,
    `${fmt(avgVsTop)} vs top quartile (avg)`,
    `${fmt(avgVsPrev)} vs previous (avg)`,
  ];

  if (continuity && governance && memory) {
    parts.push(
      `Continuity ${fmt(continuity.vsIndustry)} industry; Governance ${fmt(governance.vsIndustry)}; Memory ${fmt(memory.vsIndustry)}.`,
    );
  }

  return parts.join(' · ');
}

export function summarizeBenchmarksDetailed(
  current: PublicStateVector,
  benchmarks: BenchmarkSnapshot,
): BenchmarkSummary {
  return {
    deltas: computeBenchmarkDeltas(current, benchmarks),
    narrative: summarizeBenchmarks(current, benchmarks),
  };
}

/** Marker positions for benchmark bar UI (0–100). */
export function scoresToBenchmarkPoints(
  current: PublicStateVector,
  benchmarks: BenchmarkSnapshot,
): Record<keyof PublicDimensionScores, BenchmarkBarMarkers> {
  const keys = ['continuity', 'governance', 'memory', 'coordination', 'confidence'] as const;
  const out = {} as Record<keyof PublicDimensionScores, BenchmarkBarMarkers>;
  for (const key of keys) {
    out[key] = {
      current: current[key],
      previous: benchmarks.previousMeasurement[key],
      industry: benchmarks.industryAverage[key],
      topQuartile: benchmarks.topQuartile[key],
    };
  }
  return out;
}
