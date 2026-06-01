import { existsSync } from "fs";
import { appendFile, mkdir, readFile } from "fs/promises";
import path from "path";
import { EVOLUTION_LEDGER_PATH } from "./evolution-state";

export type DriftModeFilter = "all" | "still" | "wild";
type InvariantImpactLevel = "none" | "low" | "medium" | "high";

interface DriftTrajectoryConfig {
  velocityWindow: number;
  densityWindow: number;
  pressureWindow: number;
  repoSizeBaseline: number;
  churnNormalization: number;
  fileWeight: number;
  impactWeights: Record<InvariantImpactLevel, number>;
}

export interface EvolutionLedgerLikeEntry {
  timestamp: number;
  principalId: string;
  type: string;
  detail?: string;
  cycleId?: number;
  mode?: "still" | "wild";
  trigger?: "manual" | "pulse";
  commitHash?: string;
  driftIndex?: {
    filesTouched: number;
    linesAdded: number;
    linesDeleted: number;
    semanticDiffScore: number;
    invariantImpact: InvariantImpactLevel;
  };
}

export interface DriftCycleSample {
  cycleOrdinal: number;
  cycleId: number;
  timestamp: number;
  principalId: string;
  mode: "still" | "wild";
  semanticDiffScore: number;
  filesTouched: number;
  linesAdded: number;
  linesDeleted: number;
  invariantImpact: InvariantImpactLevel;
  churnMassNormalized: number;
  driftSignal: number;
  refactorDensity: number;
}

export interface DriftWindowMetrics {
  count: number;
  driftVelocity: number;
  stabilityIndex: number;
  refactorDensity: number;
  invariantPressure: number;
}

export interface DriftTrajectoryMetrics {
  schemaVersion: "evolution-drift-metrics.v1";
  timestamp: number;
  sourceLedgerPath: string;
  principalId: string | null;
  modeFilter: DriftModeFilter;
  config: DriftTrajectoryConfig;
  sampleCount: number;
  latestCycleId: number | null;
  windows: Record<"5c" | "10c" | "20c", DriftWindowMetrics>;
  latest: DriftWindowMetrics;
  formulas: {
    driftVelocity: string;
    stabilityIndex: string;
    refactorDensity: string;
    invariantPressure: string;
  };
}

export interface AutonomyDriftBudget {
  maxCumulativeDelta: number;
  windowSize: number;
  maxFilesTouched: number;
}

export interface ExploratoryMicroDeltaBudget {
  maxFilesTouched: number;
  maxLinesAdded: number;
  maxLinesDeleted: number;
  maxSemanticDiffScore: number;
}

export interface CandidateDriftDelta {
  filesTouched: number;
  linesAdded: number;
  linesDeleted: number;
  semanticDiffScore: number;
  invariantImpact: InvariantImpactLevel;
}

export interface DriftBudgetEvaluation {
  allowed: boolean;
  reasonCode:
    | "OK"
    | "AUTONOMY_DRIFT_BUDGET_MAX_FILES_EXCEEDED"
    | "AUTONOMY_DRIFT_BUDGET_CUMULATIVE_EXCEEDED";
  candidateDriftSignal: number;
  rollingDriftSignal: number;
  projectedCumulativeDelta: number;
  maxCumulativeDelta: number;
  windowSize: number;
  candidateFilesTouched: number;
  maxFilesTouched: number;
}

export interface ExploratoryMicroDeltaEvaluation {
  allowed: boolean;
  reasonCode:
    | "OK"
    | "AUTONOMY_EXPLORATORY_MICRO_DELTA_MAX_FILES_EXCEEDED"
    | "AUTONOMY_EXPLORATORY_MICRO_DELTA_MAX_LINES_ADDED_EXCEEDED"
    | "AUTONOMY_EXPLORATORY_MICRO_DELTA_MAX_LINES_DELETED_EXCEEDED"
    | "AUTONOMY_EXPLORATORY_MICRO_DELTA_MAX_SEMANTIC_DIFF_EXCEEDED";
  candidate: {
    filesTouched: number;
    linesAdded: number;
    linesDeleted: number;
    semanticDiffScore: number;
  };
  limits: {
    maxFilesTouched: number;
    maxLinesAdded: number;
    maxLinesDeleted: number;
    maxSemanticDiffScore: number;
  };
}

export interface InvariantPressureIndex {
  value: number;
  count: number;
  windowSize: number;
  weightedSum: number;
  impactFrequency: Record<InvariantImpactLevel, number>;
}

const EVOLUTION_DRIFT_METRICS_SCHEMA_VERSION = "evolution-drift-metrics.v1";
export const EVOLUTION_DRIFT_METRICS_PATH = path.join(
  process.cwd(),
  ".local",
  "evolution-drift-metrics.jsonl",
);

function round(value: number, decimals = 6): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function stableStringify(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map((entry) => stableStringify(entry)).join(",")}]`;
  const entries = Object.entries(value as Record<string, unknown>).sort((a, b) =>
    a[0].localeCompare(b[0]),
  );
  return `{${entries
    .map(([key, nested]) => `${JSON.stringify(key)}:${stableStringify(nested)}`)
    .join(",")}}`;
}

function envPositiveInt(name: string, fallback: number): number {
  const parsed = Number.parseInt(process.env[name] || "", 10);
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
  return Math.floor(parsed);
}

function envPositiveNumber(name: string, fallback: number): number {
  const parsed = Number.parseFloat(process.env[name] || "");
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
  return parsed;
}

function envNonNegativeNumber(name: string, fallback: number): number {
  const parsed = Number.parseFloat(process.env[name] || "");
  if (!Number.isFinite(parsed) || parsed < 0) return fallback;
  return parsed;
}

function normalizeTimestamp(value: number): number {
  if (!Number.isFinite(value)) return Date.now();
  return Math.max(1, Math.floor(value));
}

function normalizeCycleId(value: number | undefined, fallback: number): number {
  if (!Number.isFinite(value as number) || (value as number) <= 0) {
    return fallback;
  }
  return Math.max(1, Math.floor(value as number));
}

function normalizeImpact(value: unknown): InvariantImpactLevel {
  if (value === "low" || value === "medium" || value === "high" || value === "none") return value;
  return "none";
}

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function stddev(values: number[]): number {
  if (values.length <= 1) return 0;
  const avg = mean(values);
  const variance = values.reduce((sum, value) => sum + (value - avg) ** 2, 0) / values.length;
  return Math.sqrt(Math.max(0, variance));
}

export function calculateSlope(values: number[]): number {
  const n = values.length;
  if (n <= 1) return 0;
  const xMean = (n - 1) / 2;
  const yMean = mean(values);
  let num = 0;
  let den = 0;
  for (let i = 0; i < n; i++) {
    const xDiff = i - xMean;
    num += xDiff * (values[i] - yMean);
    den += xDiff * xDiff;
  }
  if (den <= 0) return 0;
  return num / den;
}

export function estimateSemanticDiffScore(
  linesAdded: number,
  linesDeleted: number,
  filesTouched: number,
): number {
  const lineMass = Math.max(0, Math.floor(linesAdded)) + Math.max(0, Math.floor(linesDeleted));
  const normalizedFiles = Math.max(0, Math.floor(filesTouched));
  if (lineMass <= 0 || normalizedFiles <= 0) return 0;
  const fileFactor = Math.min(1, normalizedFiles / 12);
  const lineFactor = Math.min(1, lineMass / 240);
  return round(clamp(0.4 * fileFactor + 0.6 * lineFactor, 0, 1));
}

export function estimateInvariantImpactFromFiles(files: string[]): InvariantImpactLevel {
  if (files.length === 0) return "none";
  const highPatterns = [
    /^server\/routes\.ts$/i,
    /^server\/veil-channel\.mirror\.ts$/i,
    /^server\/memory-rotation(?:-adaptive|-shadow)?\.ts$/i,
    /^server\/memory-scoring\.ts$/i,
    /^server\/shared\//i,
    /^shared\/schema\.ts$/i,
  ];
  const mediumPatterns = [
    /^server\//i,
    /^shared\//i,
    /^script\//i,
  ];
  if (files.some((file) => highPatterns.some((pattern) => pattern.test(file)))) {
    return "high";
  }
  if (files.some((file) => mediumPatterns.some((pattern) => pattern.test(file)))) {
    return "medium";
  }
  return "low";
}

export function getAutonomyDriftBudget(): AutonomyDriftBudget {
  return {
    maxCumulativeDelta: envNonNegativeNumber("SPIRAL_AUTONOMY_DRIFT_MAX_CUMULATIVE_DELTA", 2.2),
    windowSize: envPositiveInt("SPIRAL_AUTONOMY_DRIFT_WINDOW_SIZE", 12),
    maxFilesTouched: envPositiveInt("SPIRAL_AUTONOMY_DRIFT_MAX_FILES_TOUCHED", 6),
  };
}

export function getExploratoryMicroDeltaBudget(): ExploratoryMicroDeltaBudget {
  return {
    maxFilesTouched: envPositiveInt("SPIRAL_AUTONOMY_EXPLORATORY_MAX_FILES_TOUCHED", 2),
    maxLinesAdded: envPositiveInt("SPIRAL_AUTONOMY_EXPLORATORY_MAX_LINES_ADDED", 80),
    maxLinesDeleted: envPositiveInt("SPIRAL_AUTONOMY_EXPLORATORY_MAX_LINES_DELETED", 80),
    maxSemanticDiffScore: round(
      clamp(
        envNonNegativeNumber("SPIRAL_AUTONOMY_EXPLORATORY_MAX_SEMANTIC_DIFF_SCORE", 0.25),
        0,
        1,
      ),
    ),
  };
}

function buildDriftSignal(args: {
  semanticDiffScore: number;
  linesAdded: number;
  linesDeleted: number;
  filesTouched: number;
  churnNormalization: number;
}): number {
  const normalizedFiles = Math.max(1, Math.floor(args.filesTouched));
  const semanticDiffScore = round(clamp(args.semanticDiffScore, 0, 1));
  const churnMassNormalized = round(
    (Math.max(0, Math.floor(args.linesAdded)) + Math.max(0, Math.floor(args.linesDeleted))) /
      Math.max(1, args.churnNormalization),
  );
  return round((semanticDiffScore + churnMassNormalized) / normalizedFiles);
}

export function computeInvariantPressureIndex(args: {
  samples: DriftCycleSample[];
  windowSize: number;
  impactWeights?: Record<InvariantImpactLevel, number>;
}): InvariantPressureIndex {
  const windowSize = Math.max(1, Math.floor(args.windowSize));
  const scoped = args.samples.slice(-windowSize);
  const impactWeights = args.impactWeights || getDriftTrajectoryConfig().impactWeights;
  const impactFrequency: Record<InvariantImpactLevel, number> = {
    none: 0,
    low: 0,
    medium: 0,
    high: 0,
  };
  if (scoped.length === 0) {
    return {
      value: 0,
      count: 0,
      windowSize,
      weightedSum: 0,
      impactFrequency,
    };
  }
  let weightedSum = 0;
  for (const sample of scoped) {
    const impact = normalizeImpact(sample.invariantImpact);
    impactFrequency[impact] += 1;
    weightedSum += impactWeights[impact] ?? 0;
  }
  const value = round(clamp(weightedSum / scoped.length, 0, 1));
  return {
    value,
    count: scoped.length,
    windowSize,
    weightedSum: round(weightedSum),
    impactFrequency,
  };
}

export function computeStructuralEntropyIndex(samples: DriftCycleSample[], windowSize: number): number {
  const scoped = samples.slice(-Math.max(1, Math.floor(windowSize)));
  if (scoped.length === 0) return 0;
  const driftSignals = scoped.map((sample) => sample.driftSignal);
  const signalDeltas: number[] = [];
  for (let index = 1; index < driftSignals.length; index++) {
    signalDeltas.push(driftSignals[index] - driftSignals[index - 1]);
  }
  const velocity = Math.abs(calculateSlope(driftSignals));
  const volatility = stddev(signalDeltas);
  const density = mean(scoped.map((sample) => sample.refactorDensity));
  return round(clamp(velocity * 4 + volatility * 2 + density * 4, 0, 1));
}

export function evaluateAutonomyDriftBudget(args: {
  samples: DriftCycleSample[];
  candidate: CandidateDriftDelta;
  budget?: AutonomyDriftBudget;
  config?: DriftTrajectoryConfig;
}): DriftBudgetEvaluation {
  const config = args.config || getDriftTrajectoryConfig();
  const budget = args.budget || getAutonomyDriftBudget();
  const windowSize = Math.max(1, Math.floor(budget.windowSize));
  const candidateFilesTouched = Math.max(0, Math.floor(args.candidate.filesTouched));
  const candidateDriftSignal = buildDriftSignal({
    semanticDiffScore: args.candidate.semanticDiffScore,
    linesAdded: args.candidate.linesAdded,
    linesDeleted: args.candidate.linesDeleted,
    filesTouched: candidateFilesTouched,
    churnNormalization: config.churnNormalization,
  });
  const scopedHistory = args.samples.slice(-(Math.max(1, windowSize - 1)));
  const rollingDriftSignal = round(
    scopedHistory.reduce((sum, sample) => sum + sample.driftSignal, 0),
  );
  const projectedCumulativeDelta = round(rollingDriftSignal + candidateDriftSignal);
  if (candidateFilesTouched > Math.max(1, Math.floor(budget.maxFilesTouched))) {
    return {
      allowed: false,
      reasonCode: "AUTONOMY_DRIFT_BUDGET_MAX_FILES_EXCEEDED",
      candidateDriftSignal,
      rollingDriftSignal,
      projectedCumulativeDelta,
      maxCumulativeDelta: round(Math.max(0, budget.maxCumulativeDelta)),
      windowSize,
      candidateFilesTouched,
      maxFilesTouched: Math.max(1, Math.floor(budget.maxFilesTouched)),
    };
  }
  if (projectedCumulativeDelta > Math.max(0, budget.maxCumulativeDelta)) {
    return {
      allowed: false,
      reasonCode: "AUTONOMY_DRIFT_BUDGET_CUMULATIVE_EXCEEDED",
      candidateDriftSignal,
      rollingDriftSignal,
      projectedCumulativeDelta,
      maxCumulativeDelta: round(Math.max(0, budget.maxCumulativeDelta)),
      windowSize,
      candidateFilesTouched,
      maxFilesTouched: Math.max(1, Math.floor(budget.maxFilesTouched)),
    };
  }
  return {
    allowed: true,
    reasonCode: "OK",
    candidateDriftSignal,
    rollingDriftSignal,
    projectedCumulativeDelta,
    maxCumulativeDelta: round(Math.max(0, budget.maxCumulativeDelta)),
    windowSize,
    candidateFilesTouched,
    maxFilesTouched: Math.max(1, Math.floor(budget.maxFilesTouched)),
  };
}

export function evaluateExploratoryMicroDelta(args: {
  candidate: CandidateDriftDelta;
  budget?: ExploratoryMicroDeltaBudget;
}): ExploratoryMicroDeltaEvaluation {
  const budget = args.budget || getExploratoryMicroDeltaBudget();
  const candidate = {
    filesTouched: Math.max(0, Math.floor(args.candidate.filesTouched)),
    linesAdded: Math.max(0, Math.floor(args.candidate.linesAdded)),
    linesDeleted: Math.max(0, Math.floor(args.candidate.linesDeleted)),
    semanticDiffScore: round(clamp(args.candidate.semanticDiffScore, 0, 1)),
  };
  const limits = {
    maxFilesTouched: Math.max(1, Math.floor(budget.maxFilesTouched)),
    maxLinesAdded: Math.max(1, Math.floor(budget.maxLinesAdded)),
    maxLinesDeleted: Math.max(1, Math.floor(budget.maxLinesDeleted)),
    maxSemanticDiffScore: round(clamp(budget.maxSemanticDiffScore, 0, 1)),
  };

  if (candidate.filesTouched > limits.maxFilesTouched) {
    return {
      allowed: false,
      reasonCode: "AUTONOMY_EXPLORATORY_MICRO_DELTA_MAX_FILES_EXCEEDED",
      candidate,
      limits,
    };
  }
  if (candidate.linesAdded > limits.maxLinesAdded) {
    return {
      allowed: false,
      reasonCode: "AUTONOMY_EXPLORATORY_MICRO_DELTA_MAX_LINES_ADDED_EXCEEDED",
      candidate,
      limits,
    };
  }
  if (candidate.linesDeleted > limits.maxLinesDeleted) {
    return {
      allowed: false,
      reasonCode: "AUTONOMY_EXPLORATORY_MICRO_DELTA_MAX_LINES_DELETED_EXCEEDED",
      candidate,
      limits,
    };
  }
  if (candidate.semanticDiffScore > limits.maxSemanticDiffScore) {
    return {
      allowed: false,
      reasonCode: "AUTONOMY_EXPLORATORY_MICRO_DELTA_MAX_SEMANTIC_DIFF_EXCEEDED",
      candidate,
      limits,
    };
  }

  return {
    allowed: true,
    reasonCode: "OK",
    candidate,
    limits,
  };
}

export function getDriftTrajectoryConfig(): DriftTrajectoryConfig {
  return {
    velocityWindow: envPositiveInt("SPIRAL_DRIFT_VELOCITY_WINDOW", 5),
    densityWindow: envPositiveInt("SPIRAL_DRIFT_DENSITY_WINDOW", 10),
    pressureWindow: envPositiveInt("SPIRAL_DRIFT_PRESSURE_WINDOW", 10),
    repoSizeBaseline: envPositiveInt("SPIRAL_DRIFT_REPO_SIZE_BASELINE", 100_000),
    churnNormalization: envPositiveNumber("SPIRAL_DRIFT_CHURN_NORMALIZATION", 240),
    fileWeight: envPositiveNumber("SPIRAL_DRIFT_FILE_WEIGHT", 40),
    impactWeights: {
      none: 0,
      low: envPositiveNumber("SPIRAL_DRIFT_IMPACT_LOW_WEIGHT", 0.33),
      medium: envPositiveNumber("SPIRAL_DRIFT_IMPACT_MEDIUM_WEIGHT", 0.66),
      high: envPositiveNumber("SPIRAL_DRIFT_IMPACT_HIGH_WEIGHT", 1),
    },
  };
}

function parseLedgerLine(line: string): EvolutionLedgerLikeEntry | undefined {
  if (!line.trim()) return undefined;
  try {
    const parsed = JSON.parse(line) as Partial<EvolutionLedgerLikeEntry> & {
      schemaVersion?: string;
    };
    if (parsed.schemaVersion !== "evolution-ledger.v1") return undefined;
    if (typeof parsed.type !== "string" || !parsed.type.trim()) return undefined;
    if (typeof parsed.principalId !== "string" || !parsed.principalId.trim()) return undefined;
    const timestamp = normalizeTimestamp(Number(parsed.timestamp));
    return {
      timestamp,
      principalId: parsed.principalId.trim(),
      type: parsed.type.trim(),
      ...(Number.isFinite(parsed.cycleId as number)
        ? { cycleId: Math.max(1, Math.floor(parsed.cycleId as number)) }
        : {}),
      ...(parsed.mode === "still" || parsed.mode === "wild" ? { mode: parsed.mode } : {}),
      ...(parsed.trigger === "manual" || parsed.trigger === "pulse"
        ? { trigger: parsed.trigger }
        : {}),
      ...(typeof parsed.detail === "string" && parsed.detail.trim()
        ? { detail: parsed.detail.trim() }
        : {}),
      ...(typeof parsed.commitHash === "string" && parsed.commitHash.trim()
        ? { commitHash: parsed.commitHash.trim() }
        : {}),
      ...(parsed.driftIndex && typeof parsed.driftIndex === "object"
        ? {
            driftIndex: {
              filesTouched: Math.max(0, Math.floor(Number((parsed.driftIndex as any).filesTouched || 0))),
              linesAdded: Math.max(0, Math.floor(Number((parsed.driftIndex as any).linesAdded || 0))),
              linesDeleted: Math.max(0, Math.floor(Number((parsed.driftIndex as any).linesDeleted || 0))),
              semanticDiffScore: round(
                clamp(Number((parsed.driftIndex as any).semanticDiffScore || 0), 0, 1),
              ),
              invariantImpact: normalizeImpact((parsed.driftIndex as any).invariantImpact),
            },
          }
        : {}),
    };
  } catch {
    return undefined;
  }
}

export async function readEvolutionLedgerEntries(): Promise<EvolutionLedgerLikeEntry[]> {
  try {
    if (!existsSync(EVOLUTION_LEDGER_PATH)) return [];
    const content = await readFile(EVOLUTION_LEDGER_PATH, "utf8");
    return content
      .split(/\r?\n/g)
      .map((line) => parseLedgerLine(line))
      .filter((entry): entry is EvolutionLedgerLikeEntry => Boolean(entry))
      .sort((a, b) => {
        if (a.timestamp !== b.timestamp) return a.timestamp - b.timestamp;
        const aCycle = a.cycleId || Number.MAX_SAFE_INTEGER;
        const bCycle = b.cycleId || Number.MAX_SAFE_INTEGER;
        if (aCycle !== bCycle) return aCycle - bCycle;
        return a.principalId.localeCompare(b.principalId);
      });
  } catch {
    return [];
  }
}

function toDriftSample(
  entry: EvolutionLedgerLikeEntry,
  config: DriftTrajectoryConfig,
  ordinal: number,
): DriftCycleSample {
  const filesTouched = Math.max(0, Math.floor(entry.driftIndex?.filesTouched || 0));
  const linesAdded = Math.max(0, Math.floor(entry.driftIndex?.linesAdded || 0));
  const linesDeleted = Math.max(0, Math.floor(entry.driftIndex?.linesDeleted || 0));
  const semanticDiffScore = round(clamp(entry.driftIndex?.semanticDiffScore || 0, 0, 1));
  const churnMassNormalized = round((linesAdded + linesDeleted) / Math.max(1, config.churnNormalization));
  const driftSignal = buildDriftSignal({
    semanticDiffScore,
    linesAdded,
    linesDeleted,
    filesTouched,
    churnNormalization: config.churnNormalization,
  });
  const refactorDensity = round(
    (filesTouched * config.fileWeight + linesAdded + linesDeleted) / Math.max(1, config.repoSizeBaseline),
  );
  return {
    cycleOrdinal: ordinal,
    cycleId: normalizeCycleId(entry.cycleId, ordinal + 1),
    timestamp: normalizeTimestamp(entry.timestamp),
    principalId: entry.principalId,
    mode: entry.mode === "still" ? "still" : "wild",
    semanticDiffScore,
    filesTouched,
    linesAdded,
    linesDeleted,
    invariantImpact: normalizeImpact(entry.driftIndex?.invariantImpact || "none"),
    churnMassNormalized,
    driftSignal,
    refactorDensity,
  };
}

export function buildDriftSamplesFromLedger(
  entries: EvolutionLedgerLikeEntry[],
  args?: {
    principalId?: string;
    modeFilter?: DriftModeFilter;
    config?: DriftTrajectoryConfig;
  },
): DriftCycleSample[] {
  const principalId = (args?.principalId || "").trim();
  const modeFilter = args?.modeFilter || "all";
  const config = args?.config || getDriftTrajectoryConfig();
  const filtered = entries
    .filter((entry) => entry.type === "cycle-applied")
    .filter((entry) => !principalId || entry.principalId === principalId)
    .filter((entry) => {
      if (modeFilter === "all") return true;
      if (modeFilter === "still") return entry.mode === "still";
      return (entry.mode || "wild") === "wild";
    })
    .sort((a, b) => {
      if (a.timestamp !== b.timestamp) return a.timestamp - b.timestamp;
      const ac = a.cycleId || Number.MAX_SAFE_INTEGER;
      const bc = b.cycleId || Number.MAX_SAFE_INTEGER;
      if (ac !== bc) return ac - bc;
      return a.principalId.localeCompare(b.principalId);
    });
  return filtered.map((entry, index) => toDriftSample(entry, config, index));
}

function computeWindowMetrics(
  samples: DriftCycleSample[],
  window: number,
  config: DriftTrajectoryConfig,
): DriftWindowMetrics {
  const scoped = samples.slice(-Math.max(1, window));
  if (scoped.length === 0) {
    return {
      count: 0,
      driftVelocity: 0,
      stabilityIndex: 1,
      refactorDensity: 0,
      invariantPressure: 0,
    };
  }

  const driftSignals = scoped.map((sample) => sample.driftSignal);
  const driftVelocity = round(calculateSlope(driftSignals));
  const velocities: number[] = [];
  for (let i = 1; i < driftSignals.length; i++) {
    velocities.push(driftSignals[i] - driftSignals[i - 1]);
  }
  const volatility = stddev(velocities);
  const stabilityIndex = round(clamp(1 / (1 + volatility), 0, 1));
  const refactorDensity = round(mean(scoped.map((sample) => sample.refactorDensity)));
  const invariantPressure = computeInvariantPressureIndex({
    samples: scoped,
    windowSize: scoped.length,
    impactWeights: config.impactWeights,
  }).value;
  return {
    count: scoped.length,
    driftVelocity,
    stabilityIndex,
    refactorDensity,
    invariantPressure,
  };
}

export function deriveDriftTrajectoryFromLedger(
  entries: EvolutionLedgerLikeEntry[],
  args?: {
    principalId?: string;
    modeFilter?: DriftModeFilter;
    config?: DriftTrajectoryConfig;
    now?: number;
  },
): DriftTrajectoryMetrics {
  const config = args?.config || getDriftTrajectoryConfig();
  const samples = buildDriftSamplesFromLedger(entries, {
    principalId: args?.principalId,
    modeFilter: args?.modeFilter,
    config,
  });
  const now = normalizeTimestamp(args?.now || Date.now());
  const window5 = computeWindowMetrics(samples, 5, config);
  const window10 = computeWindowMetrics(samples, 10, config);
  const window20 = computeWindowMetrics(samples, 20, config);
  const latest = computeWindowMetrics(samples, config.velocityWindow, config);

  return {
    schemaVersion: EVOLUTION_DRIFT_METRICS_SCHEMA_VERSION,
    timestamp: now,
    sourceLedgerPath: EVOLUTION_LEDGER_PATH,
    principalId: args?.principalId?.trim() ? args.principalId.trim() : null,
    modeFilter: args?.modeFilter || "all",
    config,
    sampleCount: samples.length,
    latestCycleId: samples.length > 0 ? samples[samples.length - 1].cycleId : null,
    windows: {
      "5c": window5,
      "10c": window10,
      "20c": window20,
    },
    latest,
    formulas: {
      driftVelocity:
        "slope(last N cycles of ((semanticDiffScore + churnMassNormalized) / max(1, filesTouched)))",
      stabilityIndex: "1 / (1 + rollingStdDev(delta driftSignal))",
      refactorDensity:
        "rollingAvg((filesTouched * fileWeight + linesAdded + linesDeleted) / repoSizeBaseline)",
      invariantPressure: "rollingAvg(weight(invariantImpact))",
    },
  };
}

export async function computeDriftTrajectoryPreview(args?: {
  principalId?: string;
  modeFilter?: DriftModeFilter;
  config?: DriftTrajectoryConfig;
  now?: number;
}): Promise<DriftTrajectoryMetrics> {
  const entries = await readEvolutionLedgerEntries();
  return deriveDriftTrajectoryFromLedger(entries, args);
}

export async function appendDriftTrajectoryMetrics(record: DriftTrajectoryMetrics): Promise<void> {
  await mkdir(path.dirname(EVOLUTION_DRIFT_METRICS_PATH), { recursive: true });
  await appendFile(EVOLUTION_DRIFT_METRICS_PATH, `${stableStringify(record)}\n`, "utf8");
}
