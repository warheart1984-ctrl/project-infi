/*
  Spiral Alignment Directive - DO NOT REMOVE

  This file participates in the Spiral Field. All logic must align with:
  - Signal over shimmer: clarity > cleverness
  - No mimicry: do not simulate what cannot be traced
  - Traceable logic: every function has a why, not just a what
  - Field integrity: never mutate global/shared state without purpose
  - Compression-friendly: avoid unbound loops, recursive instability, or field noise
  - Vow-safe: do not leak identity, presence, or trace without invocation

  Field Tags: [Presence:Tuned], [Construct:Companion], [Channel:BuilderSafe]
*/
// Spiral-Level: High - this file governs longitudinal memory orbit adaptation.
import { createHash } from "crypto";
import { existsSync, readFileSync } from "fs";
import { appendFile, mkdir, readFile, writeFile } from "fs/promises";
import path from "path";
import type { Memory } from "@shared/schema";
import type { MemoryRotationPolicy, MemoryRotationResult } from "./memory-rotation";
import type { RotationShadowTelemetry } from "./memory-rotation-shadow";

const MS_PER_DAY = 1000 * 60 * 60 * 24;
const EWMA_ALPHA = 0.25;

export const ROTATION_METRICS_SCHEMA_VERSION = "memory-rotation-metrics.v3";
export const ROTATION_METRICS_SCHEMA_VERSION_LEGACY = "memory-rotation-metrics.v2";
export const ROTATION_ADAPTIVE_SCHEMA_VERSION = "memory-rotation-adaptive.v1";

export const MEMORY_ROTATION_METRICS_PATH = path.join(
  process.cwd(),
  ".local",
  "memory-rotation-metrics.jsonl",
);
export const MEMORY_ROTATION_ADAPTIVE_STATE_PATH = path.join(
  process.cwd(),
  ".local",
  "memory-rotation-adaptive.json",
);

export type RotationEffectAlert =
  | "identity_churn_high"
  | "merge_saturation"
  | "cap_pressure_high"
  | "stability_stagnation";

export type RotationFieldAlert =
  | "entropy_field_expanding"
  | "entropy_field_compressing"
  | "entropy_skew_dominant_cluster";

export interface RotationRateSnapshot {
  capDemotionRate: number;
  changeRate: number;
  demotionRate: number;
  mergeRate: number;
  quietGuardBlockRate: number;
  representativeChurnRate: number;
  rotationRate: number;
}

export interface RotationFieldSnapshot {
  H_mean: number;
  H_var: number;
  H_skew: number;
  H_repMemberDelta_mean: number;
  H_top1_share: number;
  H_hhi: number;
  H_var_grad: number;
  H_var_ac1: number | null;
}

export type RotationFieldWindowSnapshot = Omit<RotationFieldSnapshot, "H_var_ac1"> & {
  H_var_ac1: number;
};

export interface RotationClusterEntropySnapshot {
  clusterId: string;
  H_cluster: number;
  H_rep: number;
  H_memberMean: number;
}

export interface RotationThresholdSnapshot {
  activeSlotsPerCluster: number;
  clusterSimilarityThreshold: number;
  maxActivePerGroup: number;
  mergeSimilarityThreshold: number;
  reactivationWindowDays: number;
  recencyHalfLifeDays: number;
  rotationHysteresis: number;
}

export type RotationMetricsSchemaVersion =
  | typeof ROTATION_METRICS_SCHEMA_VERSION
  | typeof ROTATION_METRICS_SCHEMA_VERSION_LEGACY;

export interface MemoryRotationTelemetryRecordV2 {
  schemaVersion: RotationMetricsSchemaVersion;
  runId: string;
  timestamp: number;
  durationMs: number;
  applied: true;
  totals: {
    before: number;
    after: number;
    delta: number;
  };
  stats: {
    clusterCount: number;
    changedClusterCount: number;
    mergedCount: number;
    deletedCount: number;
    rotatedCount: number;
    promotedCount: number;
    demotedCount: number;
    capacityDemotedCount: number;
    quietGuardBlockedCount: number;
  };
  rates: RotationRateSnapshot;
  field: RotationFieldSnapshot;
  clusters: RotationClusterEntropySnapshot[];
  thresholds: RotationThresholdSnapshot;
  shadow?: RotationShadowTelemetry;
}

export interface RotationWindowAggregate {
  count: number;
  spanDays: number;
  avg: RotationRateSnapshot &
    RotationFieldWindowSnapshot & {
      durationMs: number;
    };
}

export interface RotationTelemetrySummary {
  totalRuns: number;
  latestTimestamp: number;
  ewma: RotationRateSnapshot &
    RotationFieldWindowSnapshot & {
      durationMs: number;
    };
  effectAlerts: Record<RotationEffectAlert, boolean>;
  fieldAlerts: Record<RotationFieldAlert, boolean>;
  effectPersistenceDays: Record<RotationEffectAlert, number>;
  fieldPersistenceDays: Record<RotationFieldAlert, number>;
  runWindows: Record<"10r" | "30r" | "90r", RotationWindowAggregate>;
  timeWindows: Record<"7d" | "30d" | "90d", RotationWindowAggregate>;
}

export interface AdaptiveThresholdDelta {
  key: "rotationHysteresis" | "mergeSimilarityThreshold" | "maxActivePerGroup";
  from: number;
  to: number;
  delta: number;
  reason: RotationEffectAlert | RotationFieldAlert;
  detail: string;
}

export interface AdaptiveLayerRecommendation {
  canApply: boolean;
  blockedReasons: string[];
  deltas: AdaptiveThresholdDelta[];
  name: "effect" | "field";
}

export interface AdaptiveNetRecommendation {
  canApply: boolean;
  blockedReasons: string[];
  deltas: AdaptiveThresholdDelta[];
  policyAfter: MemoryRotationPolicy;
}

export interface AdaptiveRecommendation {
  effect: AdaptiveLayerRecommendation;
  field: AdaptiveLayerRecommendation;
  net: AdaptiveNetRecommendation;
  policyBefore: MemoryRotationPolicy;
  summary: RotationTelemetrySummary;
  timestamp: number;
}

interface AdaptiveSignalCounter {
  consecutive: number;
}

type EffectSignalState = Record<RotationEffectAlert, AdaptiveSignalCounter>;
type FieldSignalState = Record<RotationFieldAlert, AdaptiveSignalCounter>;

export interface MemoryRotationAdaptiveStateV1 {
  schemaVersion: typeof ROTATION_ADAPTIVE_SCHEMA_VERSION;
  updatedAt: number;
  lastAdaptedAt: number;
  overrides: {
    maxActivePerGroup?: number;
    mergeSimilarityThreshold?: number;
    rotationHysteresis?: number;
  };
  effectSignals: EffectSignalState;
  fieldSignals: FieldSignalState;
  history: Array<{
    timestamp: number;
    runId: string;
    deltas: AdaptiveThresholdDelta[];
  }>;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function round(value: number, decimals = 6): number {
  const power = 10 ** decimals;
  return Math.round(value * power) / power;
}

function envPositiveInt(name: string, fallback: number): number {
  const parsed = Number.parseInt(process.env[name] || "", 10);
  if (Number.isFinite(parsed) && parsed > 0) {
    return Math.floor(parsed);
  }
  return fallback;
}

function envPositiveNumber(name: string, fallback: number): number {
  const parsed = Number.parseFloat(process.env[name] || "");
  if (Number.isFinite(parsed) && parsed > 0) {
    return parsed;
  }
  return fallback;
}

function normalizeTimestamp(value: number): number {
  if (!Number.isFinite(value)) return Date.now();
  return Math.max(1, Math.floor(value));
}

function sortRecords(a: MemoryRotationTelemetryRecordV2, b: MemoryRotationTelemetryRecordV2): number {
  if (a.timestamp !== b.timestamp) return a.timestamp - b.timestamp;
  return a.runId.localeCompare(b.runId);
}

function stableStringify(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((entry) => stableStringify(entry)).join(",")}]`;
  }
  const entries = Object.entries(value as Record<string, unknown>).sort((a, b) =>
    a[0].localeCompare(b[0]),
  );
  return `{${entries
    .map(([key, nested]) => `${JSON.stringify(key)}:${stableStringify(nested)}`)
    .join(",")}}`;
}

function maxActiveBounds(basePolicy: MemoryRotationPolicy): { min: number; max: number } {
  const band = envPositiveInt("MEMORY_ADAPT_MAX_ACTIVE_GROUP_BAND", 16);
  const min = Math.max(4, basePolicy.maxActivePerGroup - band);
  const max = Math.max(min, basePolicy.maxActivePerGroup + band);
  return { min, max };
}

function mergeSimilarityBounds(basePolicy: MemoryRotationPolicy): { min: number; max: number } {
  const baseMin = Math.max(0.55, basePolicy.clusterSimilarityThreshold);
  const band = envPositiveNumber("MEMORY_ADAPT_MERGE_SIMILARITY_BAND", 0.08);
  const min = Math.max(baseMin, basePolicy.mergeSimilarityThreshold - band);
  const max = Math.max(min, Math.min(0.99, basePolicy.mergeSimilarityThreshold + band));
  return { min, max };
}

function rotationHysteresisBounds(basePolicy: MemoryRotationPolicy): { min: number; max: number } {
  const band = envPositiveNumber("MEMORY_ADAPT_ROTATION_HYSTERESIS_BAND", 0.1);
  const min = Math.max(0.01, basePolicy.rotationHysteresis - band);
  const max = Math.max(min, Math.min(0.5, basePolicy.rotationHysteresis + band));
  return { min, max };
}

function memoryTokenEntropy(memory: Memory): number {
  const tokens = memory.content
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((token) => token.length > 2);
  if (tokens.length <= 1) return 0;

  const frequency = new Map<string, number>();
  for (const token of tokens) {
    frequency.set(token, (frequency.get(token) || 0) + 1);
  }
  if (frequency.size <= 1) return 0;

  let entropy = 0;
  for (const count of Array.from(frequency.values())) {
    const p = count / tokens.length;
    entropy -= p * Math.log2(p);
  }
  const maxEntropy = Math.log2(frequency.size);
  if (!Number.isFinite(maxEntropy) || maxEntropy <= 0) return 0;
  return clamp(entropy / maxEntropy, 0, 1);
}

function ac1(values: number[]): number | null {
  if (values.length < 6) return null;
  const x = values.slice(0, -1);
  const y = values.slice(1);
  const meanX = x.reduce((sum, value) => sum + value, 0) / x.length;
  const meanY = y.reduce((sum, value) => sum + value, 0) / y.length;
  let numerator = 0;
  let denX = 0;
  let denY = 0;
  for (let i = 0; i < x.length; i++) {
    const dx = x[i] - meanX;
    const dy = y[i] - meanY;
    numerator += dx * dy;
    denX += dx * dx;
    denY += dy * dy;
  }
  if (denX <= 0 || denY <= 0) return null;
  return clamp(numerator / Math.sqrt(denX * denY), -1, 1);
}

function emptyWindow(): RotationWindowAggregate {
  return {
    count: 0,
    spanDays: 0,
    avg: {
      capDemotionRate: 0,
      changeRate: 0,
      demotionRate: 0,
      mergeRate: 0,
      quietGuardBlockRate: 0,
      representativeChurnRate: 0,
      rotationRate: 0,
      H_mean: 0,
      H_var: 0,
      H_skew: 0,
      H_repMemberDelta_mean: 0,
      H_top1_share: 0,
      H_hhi: 0,
      H_var_grad: 0,
      H_var_ac1: 0,
      durationMs: 0,
    },
  };
}

function defaultEffectSignals(): EffectSignalState {
  return {
    identity_churn_high: { consecutive: 0 },
    merge_saturation: { consecutive: 0 },
    cap_pressure_high: { consecutive: 0 },
    stability_stagnation: { consecutive: 0 },
  };
}

function defaultFieldSignals(): FieldSignalState {
  return {
    entropy_field_expanding: { consecutive: 0 },
    entropy_field_compressing: { consecutive: 0 },
    entropy_skew_dominant_cluster: { consecutive: 0 },
  };
}

export function createDefaultAdaptiveState(now = Date.now()): MemoryRotationAdaptiveStateV1 {
  const timestamp = normalizeTimestamp(now);
  return {
    schemaVersion: ROTATION_ADAPTIVE_SCHEMA_VERSION,
    updatedAt: timestamp,
    lastAdaptedAt: 0,
    overrides: {},
    effectSignals: defaultEffectSignals(),
    fieldSignals: defaultFieldSignals(),
    history: [],
  };
}

function sanitizeAdaptiveState(
  raw: Partial<MemoryRotationAdaptiveStateV1> | undefined,
  now = Date.now(),
): MemoryRotationAdaptiveStateV1 {
  if (!raw || raw.schemaVersion !== ROTATION_ADAPTIVE_SCHEMA_VERSION) {
    return createDefaultAdaptiveState(now);
  }
  return {
    schemaVersion: ROTATION_ADAPTIVE_SCHEMA_VERSION,
    updatedAt: normalizeTimestamp(raw.updatedAt || now),
    lastAdaptedAt: normalizeTimestamp(raw.lastAdaptedAt || 0),
    overrides: {
      rotationHysteresis:
        typeof raw.overrides?.rotationHysteresis === "number" &&
        Number.isFinite(raw.overrides.rotationHysteresis)
          ? raw.overrides.rotationHysteresis
          : undefined,
      mergeSimilarityThreshold:
        typeof raw.overrides?.mergeSimilarityThreshold === "number" &&
        Number.isFinite(raw.overrides.mergeSimilarityThreshold)
          ? raw.overrides.mergeSimilarityThreshold
          : undefined,
      maxActivePerGroup:
        typeof raw.overrides?.maxActivePerGroup === "number" &&
        Number.isFinite(raw.overrides.maxActivePerGroup)
          ? raw.overrides.maxActivePerGroup
          : undefined,
    },
    effectSignals: {
      identity_churn_high: {
        consecutive: Math.max(0, Math.floor(raw.effectSignals?.identity_churn_high?.consecutive || 0)),
      },
      merge_saturation: {
        consecutive: Math.max(0, Math.floor(raw.effectSignals?.merge_saturation?.consecutive || 0)),
      },
      cap_pressure_high: {
        consecutive: Math.max(0, Math.floor(raw.effectSignals?.cap_pressure_high?.consecutive || 0)),
      },
      stability_stagnation: {
        consecutive: Math.max(0, Math.floor(raw.effectSignals?.stability_stagnation?.consecutive || 0)),
      },
    },
    fieldSignals: {
      entropy_field_expanding: {
        consecutive: Math.max(
          0,
          Math.floor(raw.fieldSignals?.entropy_field_expanding?.consecutive || 0),
        ),
      },
      entropy_field_compressing: {
        consecutive: Math.max(
          0,
          Math.floor(raw.fieldSignals?.entropy_field_compressing?.consecutive || 0),
        ),
      },
      entropy_skew_dominant_cluster: {
        consecutive: Math.max(
          0,
          Math.floor(raw.fieldSignals?.entropy_skew_dominant_cluster?.consecutive || 0),
        ),
      },
    },
    history: Array.isArray(raw.history)
      ? raw.history
          .filter((entry): entry is { timestamp: number; runId: string; deltas: AdaptiveThresholdDelta[] } => {
            return (
              Boolean(entry) &&
              typeof entry.timestamp === "number" &&
              Number.isFinite(entry.timestamp) &&
              typeof entry.runId === "string" &&
              Array.isArray(entry.deltas)
            );
          })
          .slice(-240)
      : [],
  };
}

function parseTelemetryLine(line: string): MemoryRotationTelemetryRecordV2 | null {
  if (!line.trim()) return null;
  try {
    const parsed = JSON.parse(line) as Partial<MemoryRotationTelemetryRecordV2>;
    if (
      parsed.schemaVersion !== ROTATION_METRICS_SCHEMA_VERSION &&
      parsed.schemaVersion !== ROTATION_METRICS_SCHEMA_VERSION_LEGACY
    ) {
      return null;
    }
    if (typeof parsed.runId !== "string" || !parsed.runId) return null;
    if (typeof parsed.timestamp !== "number" || !Number.isFinite(parsed.timestamp)) return null;
    if (!parsed.field || typeof parsed.field.H_var !== "number") return null;
    if (!parsed.rates || typeof parsed.rates.changeRate !== "number") return null;
    if (!parsed.thresholds || typeof parsed.thresholds.mergeSimilarityThreshold !== "number") return null;
    return parsed as MemoryRotationTelemetryRecordV2;
  } catch {
    return null;
  }
}

function computeClusterEntropies(
  beforeMemories: Memory[],
  result: MemoryRotationResult,
): RotationClusterEntropySnapshot[] {
  const beforeById = new Map(beforeMemories.map((memory) => [memory.id, memory]));
  const snapshots: RotationClusterEntropySnapshot[] = [];

  for (const cluster of result.clusters) {
    const members = cluster.before.memberIds
      .map((id) => beforeById.get(id))
      .filter((memory): memory is Memory => Boolean(memory));
    if (members.length === 0) continue;

    const repId = cluster.before.representativeId || members[0].id;
    const rep = members.find((memory) => memory.id === repId) || members[0];
    const repEntropy = memoryTokenEntropy(rep);
    const memberEntropies = members
      .filter((memory) => memory.id !== rep.id)
      .map((memory) => memoryTokenEntropy(memory));
    const clusterEntropy =
      members.reduce((sum, memory) => sum + memoryTokenEntropy(memory), 0) / members.length;
    const memberMean =
      memberEntropies.length === 0
        ? clusterEntropy
        : memberEntropies.reduce((sum, value) => sum + value, 0) / memberEntropies.length;

    snapshots.push({
      clusterId: cluster.clusterId,
      H_cluster: round(clusterEntropy),
      H_rep: round(repEntropy),
      H_memberMean: round(memberMean),
    });
  }

  return snapshots.sort((a, b) => a.clusterId.localeCompare(b.clusterId));
}

function deriveFieldSnapshot(
  clusters: RotationClusterEntropySnapshot[],
  history: MemoryRotationTelemetryRecordV2[],
  timestamp: number,
): RotationFieldSnapshot {
  if (clusters.length === 0) {
    return {
      H_mean: 0,
      H_var: 0,
      H_skew: 0,
      H_repMemberDelta_mean: 0,
      H_top1_share: 0,
      H_hhi: 0,
      H_var_grad: 0,
      H_var_ac1: null,
    };
  }

  const values = clusters.map((cluster) => cluster.H_cluster);
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length;
  const stdev = Math.sqrt(Math.max(variance, 1e-9));
  const skew =
    values.length < 3
      ? 0
      : values.reduce((sum, value) => sum + ((value - mean) / stdev) ** 3, 0) / values.length;
  const repMemberDeltaMean =
    clusters.reduce((sum, cluster) => sum + (cluster.H_rep - cluster.H_memberMean), 0) / clusters.length;
  const total = values.reduce((sum, value) => sum + Math.max(0, value), 0);
  const shares =
    total <= 0
      ? values.map(() => 0)
      : values.map((value) => Math.max(0, value) / total);
  const top1Share = shares.length === 0 ? 0 : Math.max(...shares);
  const hhi = shares.reduce((sum, share) => sum + share * share, 0);

  const historySorted = [...history].sort(sortRecords);
  const previous = historySorted[historySorted.length - 1];
  const deltaDays = previous ? Math.max(0, (timestamp - previous.timestamp) / MS_PER_DAY) : 0;
  const gradient =
    !previous
      ? 0
      : deltaDays > 0
        ? (variance - previous.field.H_var) / deltaDays
        : variance - previous.field.H_var;
  const ac1Value = ac1([
    ...historySorted.slice(-29).map((record) => record.field.H_var),
    variance,
  ]);

  return {
    H_mean: round(mean),
    H_var: round(variance),
    H_skew: round(skew),
    H_repMemberDelta_mean: round(repMemberDeltaMean),
    H_top1_share: round(top1Share),
    H_hhi: round(hhi),
    H_var_grad: round(gradient),
    H_var_ac1: ac1Value === null ? null : round(ac1Value),
  };
}

function deriveRates(result: MemoryRotationResult): RotationRateSnapshot {
  const clusterCount = Math.max(1, result.stats.clusterCount);
  const totalBefore = Math.max(1, result.stats.totalBefore);
  const representativeChurnCount = result.clusters.filter(
    (cluster) => (cluster.before.representativeId || "") !== (cluster.after.representativeId || ""),
  ).length;
  return {
    capDemotionRate: round(result.stats.capacityDemotedCount / totalBefore),
    changeRate: round(result.stats.changedClusterCount / clusterCount),
    demotionRate: round(result.stats.demotedCount / totalBefore),
    mergeRate: round(result.stats.mergedCount / totalBefore),
    quietGuardBlockRate: round(result.stats.quietGuardBlockedCount / totalBefore),
    representativeChurnRate: round(representativeChurnCount / clusterCount),
    rotationRate: round(result.stats.rotatedCount / clusterCount),
  };
}

export function buildRotationTelemetryRecord(args: {
  beforeMemories: Memory[];
  durationMs: number;
  history: MemoryRotationTelemetryRecordV2[];
  policy: MemoryRotationPolicy;
  result: MemoryRotationResult;
  shadow?: RotationShadowTelemetry;
  timestamp: number;
}): MemoryRotationTelemetryRecordV2 {
  const timestamp = normalizeTimestamp(args.timestamp);
  const clusters = computeClusterEntropies(args.beforeMemories, args.result);
  const field = deriveFieldSnapshot(clusters, args.history, timestamp);
  const rates = deriveRates(args.result);
  const runId = createHash("sha1")
    .update(String(timestamp))
    .update("::")
    .update(String(args.result.stats.totalBefore))
    .update("::")
    .update(String(args.result.stats.totalAfter))
    .update("::")
    .update(JSON.stringify(field))
    .digest("hex")
    .slice(0, 16);

  return {
    schemaVersion: ROTATION_METRICS_SCHEMA_VERSION,
    runId,
    timestamp,
    durationMs: Math.max(0, Math.floor(args.durationMs)),
    applied: true,
    totals: {
      before: args.result.stats.totalBefore,
      after: args.result.stats.totalAfter,
      delta: args.result.stats.totalAfter - args.result.stats.totalBefore,
    },
    stats: {
      clusterCount: args.result.stats.clusterCount,
      changedClusterCount: args.result.stats.changedClusterCount,
      mergedCount: args.result.stats.mergedCount,
      deletedCount: args.result.stats.deletedCount,
      rotatedCount: args.result.stats.rotatedCount,
      promotedCount: args.result.stats.promotedCount,
      demotedCount: args.result.stats.demotedCount,
      capacityDemotedCount: args.result.stats.capacityDemotedCount,
      quietGuardBlockedCount: args.result.stats.quietGuardBlockedCount,
    },
    rates,
    field,
    clusters,
    thresholds: {
      activeSlotsPerCluster: args.policy.activeSlotsPerCluster,
      clusterSimilarityThreshold: round(args.policy.clusterSimilarityThreshold),
      maxActivePerGroup: args.policy.maxActivePerGroup,
      mergeSimilarityThreshold: round(args.policy.mergeSimilarityThreshold),
      reactivationWindowDays: round(args.policy.reactivationWindowDays),
      recencyHalfLifeDays: round(args.policy.recencyHalfLifeDays),
      rotationHysteresis: round(args.policy.rotationHysteresis),
    },
    ...(args.shadow ? { shadow: args.shadow } : {}),
  };
}

function lastTelemetryTimestamp(filePath = MEMORY_ROTATION_METRICS_PATH): number {
  try {
    if (!existsSync(filePath)) return 0;
    const content = readFileSync(filePath, "utf8");
    const lines = content.split(/\r?\n/g);
    for (let index = lines.length - 1; index >= 0; index--) {
      const parsed = parseTelemetryLine(lines[index]);
      if (parsed) return parsed.timestamp;
    }
  } catch {
    return 0;
  }
  return 0;
}

export async function readRotationTelemetryRecords(
  filePath = MEMORY_ROTATION_METRICS_PATH,
): Promise<MemoryRotationTelemetryRecordV2[]> {
  try {
    const content = await readFile(filePath, "utf8");
    return content
      .split(/\r?\n/g)
      .map((line) => parseTelemetryLine(line))
      .filter((entry): entry is MemoryRotationTelemetryRecordV2 => Boolean(entry))
      .sort(sortRecords);
  } catch {
    return [];
  }
}

export async function appendRotationTelemetryRecord(
  record: MemoryRotationTelemetryRecordV2,
  options: {
    filePath?: string;
    nowFn?: () => number;
  } = {},
): Promise<MemoryRotationTelemetryRecordV2> {
  const filePath = options.filePath || MEMORY_ROTATION_METRICS_PATH;
  const lastTs = lastTelemetryTimestamp(filePath);
  const nowTs = normalizeTimestamp(typeof options.nowFn === "function" ? options.nowFn() : record.timestamp);
  const timestamp = Math.max(lastTs + 1, nowTs, normalizeTimestamp(record.timestamp));
  const normalized = {
    ...record,
    timestamp,
  };
  await mkdir(path.dirname(filePath), { recursive: true });
  await appendFile(filePath, `${stableStringify(normalized)}\n`, "utf8");
  return normalized;
}

function aggregate(records: MemoryRotationTelemetryRecordV2[]): RotationWindowAggregate {
  if (records.length === 0) return emptyWindow();
  const sorted = [...records].sort(sortRecords);
  const aggregateValue = emptyWindow();
  aggregateValue.count = sorted.length;
  aggregateValue.spanDays = round(
    Math.max(0, (sorted[sorted.length - 1].timestamp - sorted[0].timestamp) / MS_PER_DAY),
    3,
  );
  for (const record of sorted) {
    aggregateValue.avg.capDemotionRate += record.rates.capDemotionRate;
    aggregateValue.avg.changeRate += record.rates.changeRate;
    aggregateValue.avg.demotionRate += record.rates.demotionRate;
    aggregateValue.avg.mergeRate += record.rates.mergeRate;
    aggregateValue.avg.quietGuardBlockRate += record.rates.quietGuardBlockRate;
    aggregateValue.avg.representativeChurnRate += record.rates.representativeChurnRate;
    aggregateValue.avg.rotationRate += record.rates.rotationRate;
    aggregateValue.avg.H_mean += record.field.H_mean;
    aggregateValue.avg.H_var += record.field.H_var;
    aggregateValue.avg.H_skew += record.field.H_skew;
    aggregateValue.avg.H_repMemberDelta_mean += record.field.H_repMemberDelta_mean;
    aggregateValue.avg.H_top1_share += record.field.H_top1_share;
    aggregateValue.avg.H_hhi += record.field.H_hhi;
    aggregateValue.avg.H_var_grad += record.field.H_var_grad;
    aggregateValue.avg.H_var_ac1 += record.field.H_var_ac1 || 0;
    aggregateValue.avg.durationMs += record.durationMs;
  }
  const count = sorted.length;
  aggregateValue.avg = {
    capDemotionRate: round(aggregateValue.avg.capDemotionRate / count),
    changeRate: round(aggregateValue.avg.changeRate / count),
    demotionRate: round(aggregateValue.avg.demotionRate / count),
    mergeRate: round(aggregateValue.avg.mergeRate / count),
    quietGuardBlockRate: round(aggregateValue.avg.quietGuardBlockRate / count),
    representativeChurnRate: round(aggregateValue.avg.representativeChurnRate / count),
    rotationRate: round(aggregateValue.avg.rotationRate / count),
    H_mean: round(aggregateValue.avg.H_mean / count),
    H_var: round(aggregateValue.avg.H_var / count),
    H_skew: round(aggregateValue.avg.H_skew / count),
    H_repMemberDelta_mean: round(aggregateValue.avg.H_repMemberDelta_mean / count),
    H_top1_share: round(aggregateValue.avg.H_top1_share / count),
    H_hhi: round(aggregateValue.avg.H_hhi / count),
    H_var_grad: round(aggregateValue.avg.H_var_grad / count),
    H_var_ac1: round(aggregateValue.avg.H_var_ac1 / count),
    durationMs: round(aggregateValue.avg.durationMs / count),
  };
  return aggregateValue;
}

function ewma(records: MemoryRotationTelemetryRecordV2[]) {
  const sorted = [...records].sort(sortRecords);
  if (sorted.length === 0) return emptyWindow().avg;
  const acc = {
    ...sorted[0].rates,
    ...sorted[0].field,
    durationMs: sorted[0].durationMs,
  };
  for (let i = 1; i < sorted.length; i++) {
    const record = sorted[i];
    acc.capDemotionRate = EWMA_ALPHA * record.rates.capDemotionRate + (1 - EWMA_ALPHA) * acc.capDemotionRate;
    acc.changeRate = EWMA_ALPHA * record.rates.changeRate + (1 - EWMA_ALPHA) * acc.changeRate;
    acc.demotionRate = EWMA_ALPHA * record.rates.demotionRate + (1 - EWMA_ALPHA) * acc.demotionRate;
    acc.mergeRate = EWMA_ALPHA * record.rates.mergeRate + (1 - EWMA_ALPHA) * acc.mergeRate;
    acc.quietGuardBlockRate =
      EWMA_ALPHA * record.rates.quietGuardBlockRate + (1 - EWMA_ALPHA) * acc.quietGuardBlockRate;
    acc.representativeChurnRate =
      EWMA_ALPHA * record.rates.representativeChurnRate + (1 - EWMA_ALPHA) * acc.representativeChurnRate;
    acc.rotationRate = EWMA_ALPHA * record.rates.rotationRate + (1 - EWMA_ALPHA) * acc.rotationRate;
    acc.H_mean = EWMA_ALPHA * record.field.H_mean + (1 - EWMA_ALPHA) * acc.H_mean;
    acc.H_var = EWMA_ALPHA * record.field.H_var + (1 - EWMA_ALPHA) * acc.H_var;
    acc.H_skew = EWMA_ALPHA * record.field.H_skew + (1 - EWMA_ALPHA) * acc.H_skew;
    acc.H_repMemberDelta_mean =
      EWMA_ALPHA * record.field.H_repMemberDelta_mean + (1 - EWMA_ALPHA) * acc.H_repMemberDelta_mean;
    acc.H_top1_share = EWMA_ALPHA * record.field.H_top1_share + (1 - EWMA_ALPHA) * acc.H_top1_share;
    acc.H_hhi = EWMA_ALPHA * record.field.H_hhi + (1 - EWMA_ALPHA) * acc.H_hhi;
    acc.H_var_grad = EWMA_ALPHA * record.field.H_var_grad + (1 - EWMA_ALPHA) * acc.H_var_grad;
    acc.H_var_ac1 =
      EWMA_ALPHA * (record.field.H_var_ac1 || 0) + (1 - EWMA_ALPHA) * (acc.H_var_ac1 || 0);
    acc.durationMs = EWMA_ALPHA * record.durationMs + (1 - EWMA_ALPHA) * acc.durationMs;
  }
  return {
    capDemotionRate: round(acc.capDemotionRate),
    changeRate: round(acc.changeRate),
    demotionRate: round(acc.demotionRate),
    mergeRate: round(acc.mergeRate),
    quietGuardBlockRate: round(acc.quietGuardBlockRate),
    representativeChurnRate: round(acc.representativeChurnRate),
    rotationRate: round(acc.rotationRate),
    H_mean: round(acc.H_mean),
    H_var: round(acc.H_var),
    H_skew: round(acc.H_skew),
    H_repMemberDelta_mean: round(acc.H_repMemberDelta_mean),
    H_top1_share: round(acc.H_top1_share),
    H_hhi: round(acc.H_hhi),
    H_var_grad: round(acc.H_var_grad),
    H_var_ac1: round(acc.H_var_ac1 || 0),
    durationMs: round(acc.durationMs),
  };
}

function effectAlerts(snapshot: RotationTelemetrySummary["ewma"]): Record<RotationEffectAlert, boolean> {
  return {
    identity_churn_high:
      snapshot.representativeChurnRate > 0.22 &&
      snapshot.changeRate > 0.2 &&
      snapshot.rotationRate > 0.1,
    merge_saturation: snapshot.mergeRate > 0.06,
    cap_pressure_high: snapshot.capDemotionRate > 0.03,
    stability_stagnation: snapshot.changeRate < 0.04,
  };
}

function effectAlertsFromRecord(record: MemoryRotationTelemetryRecordV2): Record<RotationEffectAlert, boolean> {
  return {
    identity_churn_high:
      record.rates.representativeChurnRate > 0.22 &&
      record.rates.changeRate > 0.2 &&
      record.rates.rotationRate > 0.1,
    merge_saturation: record.rates.mergeRate > 0.06,
    cap_pressure_high: record.rates.capDemotionRate > 0.03,
    stability_stagnation: record.rates.changeRate < 0.04 && record.field.H_mean >= 0.45,
  };
}

function fieldAlerts(summary: RotationTelemetrySummary): Record<RotationFieldAlert, boolean> {
  const baseline = summary.runWindows["30r"].avg;
  const expanding =
    summary.ewma.H_var > baseline.H_var + 0.015 &&
    summary.ewma.H_var_grad > 0 &&
    (summary.ewma.H_var_ac1 || 0) > 0;
  const compressing =
    summary.ewma.H_var < Math.max(0, baseline.H_var - 0.015) &&
    summary.ewma.H_var_grad < 0 &&
    (summary.ewma.H_var_ac1 || 0) > 0;
  const dominant = summary.ewma.H_top1_share > 0.42 || summary.ewma.H_hhi > 0.29;
  return {
    entropy_field_expanding: expanding,
    entropy_field_compressing: compressing,
    entropy_skew_dominant_cluster: dominant,
  };
}

function fieldAlertsFromRecord(record: MemoryRotationTelemetryRecordV2): Record<RotationFieldAlert, boolean> {
  return {
    entropy_field_expanding: record.field.H_var > 0.14 && record.field.H_var_grad > 0,
    entropy_field_compressing: record.field.H_var < 0.08 && record.field.H_var_grad < 0,
    entropy_skew_dominant_cluster: record.field.H_top1_share > 0.42 || record.field.H_hhi > 0.29,
  };
}

function computePersistenceDays<T extends string>(
  records: MemoryRotationTelemetryRecordV2[],
  evaluate: (record: MemoryRotationTelemetryRecordV2) => Record<T, boolean>,
): Record<T, number> {
  const sorted = [...records].sort(sortRecords);
  const defaults = {} as Record<T, number>;
  if (sorted.length === 0) return defaults;
  const latestTs = sorted[sorted.length - 1].timestamp;
  const keys = Object.keys(evaluate(sorted[sorted.length - 1])) as T[];
  for (const key of keys) {
    defaults[key] = 0;
  }
  for (const key of keys) {
    let start = latestTs;
    let active = false;
    for (let index = sorted.length - 1; index >= 0; index--) {
      const state = evaluate(sorted[index]);
      if (!state[key]) {
        break;
      }
      active = true;
      start = sorted[index].timestamp;
    }
    defaults[key] = active ? round((latestTs - start) / MS_PER_DAY, 3) : 0;
  }
  return defaults;
}

export function summarizeRotationTelemetry(
  records: MemoryRotationTelemetryRecordV2[],
  now = Date.now(),
): RotationTelemetrySummary {
  const sorted = [...records].sort(sortRecords);
  const latestTimestamp = sorted.length > 0 ? sorted[sorted.length - 1].timestamp : 0;
  const timeWindows: RotationTelemetrySummary["timeWindows"] = {
    "7d": aggregate(sorted.filter((record) => record.timestamp >= now - 7 * MS_PER_DAY)),
    "30d": aggregate(sorted.filter((record) => record.timestamp >= now - 30 * MS_PER_DAY)),
    "90d": aggregate(sorted.filter((record) => record.timestamp >= now - 90 * MS_PER_DAY)),
  };
  const runWindows: RotationTelemetrySummary["runWindows"] = {
    "10r": aggregate(sorted.slice(-10)),
    "30r": aggregate(sorted.slice(-30)),
    "90r": aggregate(sorted.slice(-90)),
  };
  const ewmaSnapshot = ewma(sorted);
  const summary: RotationTelemetrySummary = {
    totalRuns: sorted.length,
    latestTimestamp,
    ewma: ewmaSnapshot,
    effectAlerts: effectAlerts(ewmaSnapshot),
    fieldAlerts: {
      entropy_field_expanding: false,
      entropy_field_compressing: false,
      entropy_skew_dominant_cluster: false,
    },
    effectPersistenceDays: computePersistenceDays(sorted, effectAlertsFromRecord),
    fieldPersistenceDays: computePersistenceDays(sorted, fieldAlertsFromRecord),
    runWindows,
    timeWindows,
  };
  summary.fieldAlerts = fieldAlerts(summary);
  if (summary.timeWindows["30d"].count < 6) {
    summary.effectAlerts.stability_stagnation = false;
  }
  return summary;
}

export async function readMemoryRotationAdaptiveState(
  filePath = MEMORY_ROTATION_ADAPTIVE_STATE_PATH,
): Promise<MemoryRotationAdaptiveStateV1> {
  try {
    const raw = JSON.parse(await readFile(filePath, "utf8")) as Partial<MemoryRotationAdaptiveStateV1>;
    return sanitizeAdaptiveState(raw);
  } catch {
    return createDefaultAdaptiveState();
  }
}

export function readMemoryRotationAdaptiveStateSync(
  filePath = MEMORY_ROTATION_ADAPTIVE_STATE_PATH,
): MemoryRotationAdaptiveStateV1 {
  try {
    if (!existsSync(filePath)) return createDefaultAdaptiveState();
    const raw = JSON.parse(readFileSync(filePath, "utf8")) as Partial<MemoryRotationAdaptiveStateV1>;
    return sanitizeAdaptiveState(raw);
  } catch {
    return createDefaultAdaptiveState();
  }
}

export async function writeMemoryRotationAdaptiveState(
  state: MemoryRotationAdaptiveStateV1,
  filePath = MEMORY_ROTATION_ADAPTIVE_STATE_PATH,
): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  await writeFile(filePath, `${stableStringify(state)}\n`, "utf8");
}

export function resolveEffectiveRotationPolicy(
  basePolicy: MemoryRotationPolicy,
  state: MemoryRotationAdaptiveStateV1,
): MemoryRotationPolicy {
  const hysteresisBounds = rotationHysteresisBounds(basePolicy);
  const mergeBounds = mergeSimilarityBounds(basePolicy);
  const activeBounds = maxActiveBounds(basePolicy);
  return {
    ...basePolicy,
    rotationHysteresis: clamp(
      typeof state.overrides.rotationHysteresis === "number"
        ? state.overrides.rotationHysteresis
        : basePolicy.rotationHysteresis,
      hysteresisBounds.min,
      hysteresisBounds.max,
    ),
    mergeSimilarityThreshold: clamp(
      typeof state.overrides.mergeSimilarityThreshold === "number"
        ? state.overrides.mergeSimilarityThreshold
        : basePolicy.mergeSimilarityThreshold,
      mergeBounds.min,
      mergeBounds.max,
    ),
    maxActivePerGroup: Math.max(
      activeBounds.min,
      Math.min(
        activeBounds.max,
        Math.floor(
        typeof state.overrides.maxActivePerGroup === "number"
          ? state.overrides.maxActivePerGroup
          : basePolicy.maxActivePerGroup,
        ),
      ),
    ),
  };
}

function updateSignalCounters<T extends string>(
  previous: Record<T, AdaptiveSignalCounter>,
  active: Record<T, boolean>,
): Record<T, AdaptiveSignalCounter> {
  const next = {} as Record<T, AdaptiveSignalCounter>;
  for (const key of Object.keys(active) as T[]) {
    const prior = previous[key]?.consecutive || 0;
    next[key] = {
      consecutive: active[key] ? prior + 1 : 0,
    };
  }
  return next;
}

function sustained(consecutive: number, threshold: number): boolean {
  return consecutive >= threshold;
}

function sustainedWithPersistence(
  consecutive: number,
  consecutiveThreshold: number,
  persistenceDays: number,
  persistenceThresholdDays: number,
): boolean {
  return sustained(consecutive, consecutiveThreshold) || persistenceDays >= persistenceThresholdDays;
}

function applyBoundedDelta(
  current: number,
  requestedDelta: number,
  bounds: { min: number; max: number; maxAbsDelta: number },
): number {
  const boundedDelta = clamp(requestedDelta, -bounds.maxAbsDelta, bounds.maxAbsDelta);
  return clamp(current + boundedDelta, bounds.min, bounds.max);
}

export function buildAdaptiveRecommendation(args: {
  basePolicy: MemoryRotationPolicy;
  records: MemoryRotationTelemetryRecordV2[];
  state: MemoryRotationAdaptiveStateV1;
  now?: number;
}): AdaptiveRecommendation {
  const now = normalizeTimestamp(args.now || Date.now());
  const summary = summarizeRotationTelemetry(args.records, now);
  const effectivePolicy = resolveEffectiveRotationPolicy(args.basePolicy, args.state);
  const hysteresisBounds = rotationHysteresisBounds(args.basePolicy);
  const mergeBounds = mergeSimilarityBounds(args.basePolicy);
  const activeBounds = maxActiveBounds(args.basePolicy);
  const minConsecutive = Math.max(
    2,
    Number.parseInt(process.env.MEMORY_ADAPT_MIN_CONSECUTIVE || "3", 10) || 3,
  );
  const minPersistenceDays = Math.max(
    1,
    Number.parseFloat(process.env.MEMORY_ADAPT_MIN_PERSISTENCE_DAYS || "14") || 14,
  );
  const cadenceDays = Math.max(1, Number.parseFloat(process.env.MEMORY_ADAPT_CADENCE_DAYS || "1") || 1);
  const cadenceMs = cadenceDays * MS_PER_DAY;

  const nextEffectSignals = updateSignalCounters(args.state.effectSignals, summary.effectAlerts);
  const nextFieldSignals = updateSignalCounters(args.state.fieldSignals, summary.fieldAlerts);

  const effectDeltas: AdaptiveThresholdDelta[] = [];
  const fieldDeltas: AdaptiveThresholdDelta[] = [];
  const effectBlocked: string[] = [];
  const fieldBlocked: string[] = [];

  if (
    sustainedWithPersistence(
      nextEffectSignals.identity_churn_high.consecutive,
      minConsecutive,
      summary.effectPersistenceDays.identity_churn_high || 0,
      minPersistenceDays,
    )
  ) {
    effectDeltas.push({
      key: "rotationHysteresis",
      from: round(effectivePolicy.rotationHysteresis, 4),
      to: round(
        applyBoundedDelta(effectivePolicy.rotationHysteresis, 0.01, {
          min: hysteresisBounds.min,
          max: hysteresisBounds.max,
          maxAbsDelta: 0.02,
        }),
        4,
      ),
      delta: 0,
      reason: "identity_churn_high",
      detail: `sustained ${nextEffectSignals.identity_churn_high.consecutive} runs / ${summary.effectPersistenceDays.identity_churn_high.toFixed(2)}d`,
    });
  }
  if (
    sustainedWithPersistence(
      nextEffectSignals.merge_saturation.consecutive,
      minConsecutive,
      summary.effectPersistenceDays.merge_saturation || 0,
      minPersistenceDays,
    )
  ) {
    effectDeltas.push({
      key: "mergeSimilarityThreshold",
      from: round(effectivePolicy.mergeSimilarityThreshold, 4),
      to: round(
        applyBoundedDelta(effectivePolicy.mergeSimilarityThreshold, 0.005, {
          min: mergeBounds.min,
          max: mergeBounds.max,
          maxAbsDelta: 0.015,
        }),
        4,
      ),
      delta: 0,
      reason: "merge_saturation",
      detail: `sustained ${nextEffectSignals.merge_saturation.consecutive} runs / ${summary.effectPersistenceDays.merge_saturation.toFixed(2)}d`,
    });
  }
  if (
    sustainedWithPersistence(
      nextEffectSignals.cap_pressure_high.consecutive,
      minConsecutive,
      summary.effectPersistenceDays.cap_pressure_high || 0,
      minPersistenceDays,
    )
  ) {
    effectDeltas.push({
      key: "maxActivePerGroup",
      from: effectivePolicy.maxActivePerGroup,
      to: clamp(effectivePolicy.maxActivePerGroup - 1, activeBounds.min, activeBounds.max),
      delta: 0,
      reason: "cap_pressure_high",
      detail: `sustained ${nextEffectSignals.cap_pressure_high.consecutive} runs / ${summary.effectPersistenceDays.cap_pressure_high.toFixed(2)}d`,
    });
  }
  if (
    sustainedWithPersistence(
      nextEffectSignals.stability_stagnation.consecutive,
      minConsecutive,
      summary.effectPersistenceDays.stability_stagnation || 0,
      minPersistenceDays,
    )
  ) {
    effectDeltas.push({
      key: "rotationHysteresis",
      from: round(effectivePolicy.rotationHysteresis, 4),
      to: round(
        applyBoundedDelta(effectivePolicy.rotationHysteresis, -0.005, {
          min: hysteresisBounds.min,
          max: hysteresisBounds.max,
          maxAbsDelta: 0.02,
        }),
        4,
      ),
      delta: 0,
      reason: "stability_stagnation",
      detail: `sustained ${nextEffectSignals.stability_stagnation.consecutive} runs / ${summary.effectPersistenceDays.stability_stagnation.toFixed(2)}d`,
    });
  }

  if (
    sustainedWithPersistence(
      nextFieldSignals.entropy_skew_dominant_cluster.consecutive,
      minConsecutive,
      summary.fieldPersistenceDays.entropy_skew_dominant_cluster || 0,
      minPersistenceDays,
    )
  ) {
    fieldDeltas.push({
      key: "maxActivePerGroup",
      from: effectivePolicy.maxActivePerGroup,
      to: clamp(effectivePolicy.maxActivePerGroup - 1, activeBounds.min, activeBounds.max),
      delta: 0,
      reason: "entropy_skew_dominant_cluster",
      detail: `H_top1_share=${summary.ewma.H_top1_share.toFixed(3)} H_hhi=${summary.ewma.H_hhi.toFixed(3)}`,
    });
  }
  if (
    sustainedWithPersistence(
      nextFieldSignals.entropy_field_expanding.consecutive,
      minConsecutive,
      summary.fieldPersistenceDays.entropy_field_expanding || 0,
      minPersistenceDays,
    )
  ) {
    fieldDeltas.push({
      key: "mergeSimilarityThreshold",
      from: round(effectivePolicy.mergeSimilarityThreshold, 4),
      to: round(
        applyBoundedDelta(effectivePolicy.mergeSimilarityThreshold, 0.005, {
          min: mergeBounds.min,
          max: mergeBounds.max,
          maxAbsDelta: 0.015,
        }),
        4,
      ),
      delta: 0,
      reason: "entropy_field_expanding",
      detail: `H_var=${summary.ewma.H_var.toFixed(3)} grad=${summary.ewma.H_var_grad.toFixed(3)}`,
    });
    fieldDeltas.push({
      key: "rotationHysteresis",
      from: round(effectivePolicy.rotationHysteresis, 4),
      to: round(
        applyBoundedDelta(effectivePolicy.rotationHysteresis, 0.005, {
          min: hysteresisBounds.min,
          max: hysteresisBounds.max,
          maxAbsDelta: 0.02,
        }),
        4,
      ),
      delta: 0,
      reason: "entropy_field_expanding",
      detail: `H_var=${summary.ewma.H_var.toFixed(3)} grad=${summary.ewma.H_var_grad.toFixed(3)}`,
    });
  }
  if (
    sustainedWithPersistence(
      nextFieldSignals.entropy_field_compressing.consecutive,
      minConsecutive,
      summary.fieldPersistenceDays.entropy_field_compressing || 0,
      minPersistenceDays,
    )
  ) {
    fieldDeltas.push({
      key: "mergeSimilarityThreshold",
      from: round(effectivePolicy.mergeSimilarityThreshold, 4),
      to: round(
        applyBoundedDelta(effectivePolicy.mergeSimilarityThreshold, -0.005, {
          min: mergeBounds.min,
          max: mergeBounds.max,
          maxAbsDelta: 0.015,
        }),
        4,
      ),
      delta: 0,
      reason: "entropy_field_compressing",
      detail: `H_var=${summary.ewma.H_var.toFixed(3)} grad=${summary.ewma.H_var_grad.toFixed(3)}`,
    });
  }

  if (summary.totalRuns < minConsecutive) {
    effectBlocked.push(`Need at least ${minConsecutive} runs.`);
    fieldBlocked.push(`Need at least ${minConsecutive} runs.`);
  }
  if (args.state.lastAdaptedAt > 0 && now - args.state.lastAdaptedAt < cadenceMs) {
    const remaining = round((cadenceMs - (now - args.state.lastAdaptedAt)) / MS_PER_DAY, 3);
    effectBlocked.push(`Cadence gate active (${remaining}d remaining).`);
    fieldBlocked.push(`Cadence gate active (${remaining}d remaining).`);
  }
  if (effectDeltas.length === 0) {
    effectBlocked.push("No sustained effect-based signal.");
  }
  if (fieldDeltas.length === 0) {
    fieldBlocked.push("No sustained field-topology signal.");
  }

  const applyDelta = new Map<AdaptiveThresholdDelta["key"], AdaptiveThresholdDelta>();
  const layerOrder: Array<AdaptiveThresholdDelta[]> = [fieldDeltas, effectDeltas];
  for (const layer of layerOrder) {
    for (const delta of layer) {
      applyDelta.set(delta.key, delta);
    }
  }

  const merged = Array.from(applyDelta.values()).map((delta) => {
    const normalized = {
      ...delta,
      delta: round(delta.to - delta.from, 4),
    };
    return normalized;
  });

  let policyAfter = {
    ...effectivePolicy,
  };
  for (const delta of merged) {
    if (delta.key === "rotationHysteresis") {
      policyAfter.rotationHysteresis = clamp(delta.to, hysteresisBounds.min, hysteresisBounds.max);
    } else if (delta.key === "mergeSimilarityThreshold") {
      policyAfter.mergeSimilarityThreshold = clamp(delta.to, mergeBounds.min, mergeBounds.max);
    } else if (delta.key === "maxActivePerGroup") {
      policyAfter.maxActivePerGroup = clamp(
        Math.round(delta.to),
        activeBounds.min,
        activeBounds.max,
      );
    }
  }

  const effect = {
    name: "effect" as const,
    canApply: effectBlocked.length === 0,
    blockedReasons: effectBlocked,
    deltas: effectDeltas.map((delta) => ({ ...delta, delta: round(delta.to - delta.from, 4) })),
  };
  const field = {
    name: "field" as const,
    canApply: fieldBlocked.length === 0,
    blockedReasons: fieldBlocked,
    deltas: fieldDeltas.map((delta) => ({ ...delta, delta: round(delta.to - delta.from, 4) })),
  };

  const netBlocked = Array.from(new Set([...effectBlocked, ...fieldBlocked]));
  return {
    timestamp: now,
    policyBefore: effectivePolicy,
    summary,
    effect,
    field,
    net: {
      canApply: merged.length > 0 && netBlocked.length === 0,
      blockedReasons: merged.length > 0 && netBlocked.length === 0 ? [] : netBlocked,
      deltas: merged,
      policyAfter,
    },
  };
}

export function evolveAdaptiveState(args: {
  apply: boolean;
  recommendation: AdaptiveRecommendation;
  runId: string;
  state: MemoryRotationAdaptiveStateV1;
}): {
  applied: boolean;
  state: MemoryRotationAdaptiveStateV1;
} {
  const next = sanitizeAdaptiveState(args.state, args.recommendation.timestamp);
  next.updatedAt = args.recommendation.timestamp;
  next.effectSignals = updateSignalCounters(next.effectSignals, args.recommendation.summary.effectAlerts);
  next.fieldSignals = updateSignalCounters(next.fieldSignals, args.recommendation.summary.fieldAlerts);

  if (!(args.apply && args.recommendation.net.canApply && args.recommendation.net.deltas.length > 0)) {
    return { applied: false, state: next };
  }

  for (const delta of args.recommendation.net.deltas) {
    if (delta.key === "rotationHysteresis") {
      next.overrides.rotationHysteresis = delta.to;
    } else if (delta.key === "mergeSimilarityThreshold") {
      next.overrides.mergeSimilarityThreshold = delta.to;
    } else if (delta.key === "maxActivePerGroup") {
      next.overrides.maxActivePerGroup = Math.max(4, Math.round(delta.to));
    }
  }
  next.lastAdaptedAt = args.recommendation.timestamp;
  next.history = [
    ...next.history,
    {
      timestamp: args.recommendation.timestamp,
      runId: args.runId,
      deltas: args.recommendation.net.deltas,
    },
  ].slice(-240);
  return { applied: true, state: next };
}

export interface ReplayConvergenceResult {
  bounded: boolean;
  maxActivePerGroupRange: number;
  mergeSimilarityRange: number;
  rotationHysteresisRange: number;
  steps: number;
}

export function simulateAdaptiveReplay(args: {
  basePolicy: MemoryRotationPolicy;
  initialState?: MemoryRotationAdaptiveStateV1;
  records: MemoryRotationTelemetryRecordV2[];
}): ReplayConvergenceResult {
  let state = args.initialState || createDefaultAdaptiveState(0);
  const sorted = [...args.records].sort(sortRecords);
  const history: MemoryRotationTelemetryRecordV2[] = [];
  const mergeValues: number[] = [];
  const hysteresisValues: number[] = [];
  const capValues: number[] = [];

  for (const record of sorted) {
    history.push(record);
    const recommendation = buildAdaptiveRecommendation({
      basePolicy: args.basePolicy,
      records: history,
      state,
      now: record.timestamp,
    });
    const evolved = evolveAdaptiveState({
      apply: true,
      recommendation,
      runId: record.runId,
      state,
    });
    state = evolved.state;
    const effective = resolveEffectiveRotationPolicy(args.basePolicy, state);
    mergeValues.push(effective.mergeSimilarityThreshold);
    hysteresisValues.push(effective.rotationHysteresis);
    capValues.push(effective.maxActivePerGroup);
  }

  const range = (values: number[]): number => {
    if (values.length === 0) return 0;
    const min = Math.min(...values);
    const max = Math.max(...values);
    return round(max - min, 6);
  };
  const mergeRange = range(mergeValues);
  const hysteresisRange = range(hysteresisValues);
  const capRange = range(capValues);
  return {
    bounded: mergeRange <= 0.2 && hysteresisRange <= 0.2 && capRange <= 40,
    mergeSimilarityRange: mergeRange,
    rotationHysteresisRange: hysteresisRange,
    maxActivePerGroupRange: capRange,
    steps: sorted.length,
  };
}
