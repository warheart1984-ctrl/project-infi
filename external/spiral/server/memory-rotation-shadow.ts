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
// Spiral-Level: High - this file measures semantic shadow telemetry only (no mutation authority).
import { createHash } from "crypto";
import { existsSync, readFileSync } from "fs";
import { appendFile, mkdir, readFile } from "fs/promises";
import path from "path";
import type { Memory } from "@shared/schema";
import type { MemoryRotationResult } from "./memory-rotation";
import { tokenizeMemoryForRotation } from "./memory-rotation";

const MS_PER_DAY = 1000 * 60 * 60 * 24;
const EWMA_ALPHA = 0.125;
const DEFAULT_DISAGREEMENT_THRESHOLD = 0.15;
const DEFAULT_EMBEDDING_DIMENSION = 96;

const EMBEDDING_CACHE_SCHEMA_VERSION = "memory-embeddings.v1";

export const MEMORY_EMBEDDING_CACHE_PATH = path.join(
  process.cwd(),
  ".local",
  "memory-embeddings.v1.jsonl",
);

export type ShadowDisagreementBucket =
  | "SEMANTIC_STRONGER_THAN_LEXICAL"
  | "LEXICAL_STRONGER_THAN_SEMANTIC"
  | "BOTH_STRONG"
  | "BOTH_WEAK"
  | "NEAR_MATCH";

export interface RotationShadowPairSample {
  clusterId: string;
  aId: string;
  bId: string;
  aContent: string;
  bContent: string;
  lexicalSimilarity: number;
  semanticSimilarity: number;
  disagreement: number;
  bucket: ShadowDisagreementBucket;
}

export interface RotationShadowClusterTelemetry {
  clusterId: string;
  lexical_mean: number;
  semantic_mean: number;
  mean_disagreement: number;
  members: string[];
  semantic_suggestion?: {
    score: number;
    pairs: Array<{
      aId: string;
      bId: string;
      lexicalSimilarity: number;
      semanticSimilarity: number;
      disagreement: number;
    }>;
  };
}

export interface RotationShadowSemanticStats {
  semantic_mean: number;
  semantic_var: number;
  lexical_mean: number;
  lexical_var: number;
  mean_disagreement: number;
  disagreement_rate: number;
  semantic_top1_share: number;
}

export interface RotationShadowTelemetry {
  embeddingModel: string;
  semantic_stats: RotationShadowSemanticStats;
  disagreement_buckets: Record<ShadowDisagreementBucket, number>;
  clusters: RotationShadowClusterTelemetry[];
}

export interface RotationShadowTelemetrySummary {
  totalRuns: number;
  latestTimestamp: number;
  embeddingModel: string | null;
  ewma: RotationShadowSemanticStats;
  disagreement_buckets: Record<ShadowDisagreementBucket, number>;
  runWindows: Record<"10r" | "30r" | "90r", RotationShadowWindowAggregate>;
  timeWindows: Record<"7d" | "30d" | "90d", RotationShadowWindowAggregate>;
}

export interface RotationShadowWindowAggregate {
  count: number;
  spanDays: number;
  avg: RotationShadowSemanticStats;
}

interface EmbeddingCacheRecord {
  schemaVersion: typeof EMBEDDING_CACHE_SCHEMA_VERSION;
  memoryId: string;
  contentHash: string;
  model: string;
  dimension: number;
  timestamp: number;
  vector: number[];
}

function envPositiveNumber(name: string, fallback: number): number {
  const parsed = Number.parseFloat(process.env[name] || "");
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
  return parsed;
}

function envPositiveInt(name: string, fallback: number): number {
  const parsed = Number.parseInt(process.env[name] || "", 10);
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
  return Math.floor(parsed);
}

function round(value: number, decimals = 6): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

function normalizeTimestamp(value: number): number {
  if (!Number.isFinite(value)) return Date.now();
  return Math.max(1, Math.floor(value));
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

function cosine(a: number[], b: number[]): number {
  if (a.length === 0 || b.length === 0 || a.length !== b.length) return 0;
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  const denom = Math.sqrt(normA) * Math.sqrt(normB);
  if (!Number.isFinite(denom) || denom <= 0) return 0;
  return round(dot / denom);
}

function setSimilarity(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 || b.size === 0) return 0;
  let overlap = 0;
  for (const token of Array.from(a)) {
    if (b.has(token)) overlap += 1;
  }
  if (overlap === 0) return 0;
  const union = new Set([...Array.from(a), ...Array.from(b)]).size;
  const jaccard = union > 0 ? overlap / union : 0;
  const minSize = Math.min(a.size, b.size);
  const containment = minSize > 0 ? overlap / minSize : 0;
  return round(Math.max(jaccard, containment * 0.92));
}

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function variance(values: number[]): number {
  if (values.length === 0) return 0;
  const m = mean(values);
  return values.reduce((sum, value) => sum + (value - m) ** 2, 0) / values.length;
}

function classifyBucket(
  lexical: number,
  semantic: number,
  disagreement: number,
  disagreementThreshold: number,
): ShadowDisagreementBucket {
  const strong = 0.6;
  const weak = 0.35;
  if (lexical >= strong && semantic >= strong) return "BOTH_STRONG";
  if (lexical <= weak && semantic <= weak) return "BOTH_WEAK";
  if (semantic - lexical >= disagreementThreshold) return "SEMANTIC_STRONGER_THAN_LEXICAL";
  if (lexical - semantic >= disagreementThreshold) return "LEXICAL_STRONGER_THAN_SEMANTIC";
  return "NEAR_MATCH";
}

function emptyBuckets(): Record<ShadowDisagreementBucket, number> {
  return {
    SEMANTIC_STRONGER_THAN_LEXICAL: 0,
    LEXICAL_STRONGER_THAN_SEMANTIC: 0,
    BOTH_STRONG: 0,
    BOTH_WEAK: 0,
    NEAR_MATCH: 0,
  };
}

function emptyStats(): RotationShadowSemanticStats {
  return {
    semantic_mean: 0,
    semantic_var: 0,
    lexical_mean: 0,
    lexical_var: 0,
    mean_disagreement: 0,
    disagreement_rate: 0,
    semantic_top1_share: 0,
  };
}

function normalizeContentForHash(content: string): string {
  return content.replace(/\s+/g, " ").trim().toLowerCase();
}

function embeddingContentHash(content: string): string {
  return createHash("sha1").update(normalizeContentForHash(content)).digest("hex");
}

function normalizeVector(vector: number[], dimension: number): number[] {
  const normalized = new Array<number>(dimension).fill(0);
  for (let i = 0; i < dimension; i++) {
    const value = Number.isFinite(vector[i]) ? vector[i] : 0;
    normalized[i] = value;
  }
  let norm = 0;
  for (const value of normalized) {
    norm += value * value;
  }
  norm = Math.sqrt(norm);
  if (!Number.isFinite(norm) || norm <= 0) return normalized.map(() => 0);
  return normalized.map((value) => round(value / norm));
}

function localHashEmbedding(content: string, model: string, dimension: number): number[] {
  const tokens = content
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((token) => token.length > 1);
  const vector = new Array<number>(dimension).fill(0);
  if (tokens.length === 0) return vector;
  for (const token of tokens) {
    const digest = createHash("sha1")
      .update(model)
      .update("::")
      .update(token)
      .digest();
    for (let i = 0; i < dimension; i++) {
      const byte = digest[i % digest.length];
      const sign = byte % 2 === 0 ? 1 : -1;
      const magnitude = ((byte >>> 1) + 1) / 128;
      vector[i] += sign * magnitude;
    }
  }
  return normalizeVector(vector, dimension);
}

function parseCacheLine(line: string): EmbeddingCacheRecord | null {
  if (!line.trim()) return null;
  try {
    const parsed = JSON.parse(line) as Partial<EmbeddingCacheRecord>;
    if (parsed.schemaVersion !== EMBEDDING_CACHE_SCHEMA_VERSION) return null;
    if (typeof parsed.memoryId !== "string" || !parsed.memoryId) return null;
    if (typeof parsed.contentHash !== "string" || !parsed.contentHash) return null;
    if (typeof parsed.model !== "string" || !parsed.model) return null;
    if (typeof parsed.dimension !== "number" || !Number.isFinite(parsed.dimension) || parsed.dimension <= 0)
      return null;
    if (!Array.isArray(parsed.vector) || parsed.vector.length !== parsed.dimension) return null;
    return parsed as EmbeddingCacheRecord;
  } catch {
    return null;
  }
}

async function readEmbeddingCache(filePath: string): Promise<Map<string, EmbeddingCacheRecord>> {
  try {
    const content = await readFile(filePath, "utf8");
    const map = new Map<string, EmbeddingCacheRecord>();
    for (const line of content.split(/\r?\n/g)) {
      const parsed = parseCacheLine(line);
      if (!parsed) continue;
      map.set(parsed.memoryId, parsed);
    }
    return map;
  } catch {
    return new Map();
  }
}

function readEmbeddingCacheSync(filePath: string): Map<string, EmbeddingCacheRecord> {
  try {
    if (!existsSync(filePath)) return new Map();
    const content = readFileSync(filePath, "utf8");
    const map = new Map<string, EmbeddingCacheRecord>();
    for (const line of content.split(/\r?\n/g)) {
      const parsed = parseCacheLine(line);
      if (!parsed) continue;
      map.set(parsed.memoryId, parsed);
    }
    return map;
  } catch {
    return new Map();
  }
}

async function appendEmbeddingCache(
  filePath: string,
  records: EmbeddingCacheRecord[],
): Promise<void> {
  if (records.length === 0) return;
  await mkdir(path.dirname(filePath), { recursive: true });
  const sorted = [...records].sort((a, b) => a.memoryId.localeCompare(b.memoryId));
  const payload = `${sorted.map((record) => stableStringify(record)).join("\n")}\n`;
  await appendFile(filePath, payload, "utf8");
}

export async function computeRotationShadowTelemetry(args: {
  memories: Memory[];
  result: MemoryRotationResult;
  sampleSize?: number;
  includeSample?: boolean;
  persistCache?: boolean;
  cachePath?: string;
  model?: string;
  dimension?: number;
  disagreementThreshold?: number;
  now?: number;
  embedder?: (memory: Memory, ctx: { model: string; dimension: number }) => number[];
}): Promise<{
  telemetry: RotationShadowTelemetry;
  sample: RotationShadowPairSample[];
}> {
  const model = (args.model || process.env.MEMORY_EMBEDDING_MODEL_PIN || "local-hash-embed.v1.0.0").trim();
  const dimension = Math.max(
    16,
    Math.min(2048, args.dimension || envPositiveInt("MEMORY_EMBEDDING_DIMENSION", DEFAULT_EMBEDDING_DIMENSION)),
  );
  const now = normalizeTimestamp(args.now || Date.now());
  const disagreementThreshold = Math.max(
    0.01,
    Math.min(1, args.disagreementThreshold || envPositiveNumber("MEMORY_SHADOW_DISAGREE_THRESH", DEFAULT_DISAGREEMENT_THRESHOLD)),
  );
  const includeSample = args.includeSample === true;
  const sampleSize = Math.max(1, args.sampleSize || 20);
  const cachePath = args.cachePath || MEMORY_EMBEDDING_CACHE_PATH;
  const persistCache = args.persistCache === true;

  const memberIds = new Set<string>();
  for (const cluster of args.result.clusters) {
    for (const id of cluster.after.memberIds) memberIds.add(id);
  }
  const allById = new Map(args.memories.map((memory) => [memory.id, memory]));
  const clusteredMemories = Array.from(memberIds)
    .map((id) => allById.get(id))
    .filter((memory): memory is Memory => Boolean(memory));

  const cache = persistCache
    ? await readEmbeddingCache(cachePath)
    : readEmbeddingCacheSync(cachePath);
  const embeddingById = new Map<string, number[]>();
  const cacheUpdates: EmbeddingCacheRecord[] = [];
  for (const memory of clusteredMemories) {
    const contentHash = embeddingContentHash(memory.content);
    const cached = cache.get(memory.id);
    if (
      cached &&
      cached.model === model &&
      cached.contentHash === contentHash &&
      cached.dimension === dimension &&
      cached.vector.length === dimension
    ) {
      embeddingById.set(memory.id, normalizeVector(cached.vector, dimension));
      continue;
    }
    const vector = normalizeVector(
      args.embedder ? args.embedder(memory, { model, dimension }) : localHashEmbedding(memory.content, model, dimension),
      dimension,
    );
    embeddingById.set(memory.id, vector);
    cacheUpdates.push({
      schemaVersion: EMBEDDING_CACHE_SCHEMA_VERSION,
      memoryId: memory.id,
      contentHash,
      model,
      dimension,
      timestamp: now,
      vector,
    });
  }
  if (persistCache) {
    await appendEmbeddingCache(cachePath, cacheUpdates);
  }

  const tokenById = new Map<string, Set<string>>();
  for (const memory of clusteredMemories) {
    tokenById.set(memory.id, tokenizeMemoryForRotation(memory));
  }

  const buckets = emptyBuckets();
  const clusters: RotationShadowClusterTelemetry[] = [];
  const sample: RotationShadowPairSample[] = [];
  const lexicalMeans: number[] = [];
  const semanticMeans: number[] = [];
  const disagreementMeans: number[] = [];

  for (const cluster of args.result.clusters) {
    const ids = [...cluster.after.memberIds].sort((a, b) => a.localeCompare(b));
    const pairRows: RotationShadowPairSample[] = [];
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        const aId = ids[i];
        const bId = ids[j];
        const aMemory = allById.get(aId);
        const bMemory = allById.get(bId);
        if (!aMemory || !bMemory) continue;
        const lexical = setSimilarity(tokenById.get(aId) || new Set(), tokenById.get(bId) || new Set());
        const semantic = cosine(embeddingById.get(aId) || [], embeddingById.get(bId) || []);
        const disagreement = round(Math.abs(lexical - semantic));
        const bucket = classifyBucket(lexical, semantic, disagreement, disagreementThreshold);
        buckets[bucket] += 1;
        pairRows.push({
          clusterId: cluster.clusterId,
          aId,
          bId,
          aContent: aMemory.content,
          bContent: bMemory.content,
          lexicalSimilarity: lexical,
          semanticSimilarity: semantic,
          disagreement,
          bucket,
        });
      }
    }

    const lexicalValues = pairRows.map((row) => row.lexicalSimilarity);
    const semanticValues = pairRows.map((row) => row.semanticSimilarity);
    const disagreementValues = pairRows.map((row) => row.disagreement);
    const lexicalMean = round(mean(lexicalValues));
    const semanticMean = round(mean(semanticValues));
    const meanDisagreement = round(mean(disagreementValues));
    lexicalMeans.push(lexicalMean);
    semanticMeans.push(semanticMean);
    disagreementMeans.push(meanDisagreement);

    const topSuggestions = [...pairRows]
      .sort((a, b) => {
        if (b.semanticSimilarity !== a.semanticSimilarity) return b.semanticSimilarity - a.semanticSimilarity;
        if (b.disagreement !== a.disagreement) return b.disagreement - a.disagreement;
        if (a.aId !== b.aId) return a.aId.localeCompare(b.aId);
        return a.bId.localeCompare(b.bId);
      })
      .slice(0, 3)
      .map((row) => ({
        aId: row.aId,
        bId: row.bId,
        lexicalSimilarity: row.lexicalSimilarity,
        semanticSimilarity: row.semanticSimilarity,
        disagreement: row.disagreement,
      }));

    clusters.push({
      clusterId: cluster.clusterId,
      lexical_mean: lexicalMean,
      semantic_mean: semanticMean,
      mean_disagreement: meanDisagreement,
      members: ids,
      ...(topSuggestions.length > 0
        ? {
            semantic_suggestion: {
              score: round(topSuggestions[0].semanticSimilarity),
              pairs: topSuggestions,
            },
          }
        : {}),
    });

    if (includeSample) {
      sample.push(...pairRows);
    }
  }

  const totalSemantic = semanticMeans.reduce((sum, value) => sum + Math.max(0, value), 0);
  const topSemanticShare = totalSemantic <= 0 ? 0 : Math.max(...semanticMeans.map((value) => Math.max(0, value) / totalSemantic));
  const disagreementRate =
    disagreementMeans.length === 0
      ? 0
      : disagreementMeans.filter((value) => value > disagreementThreshold).length / disagreementMeans.length;
  const telemetry: RotationShadowTelemetry = {
    embeddingModel: model,
    semantic_stats: {
      semantic_mean: round(mean(semanticMeans)),
      semantic_var: round(variance(semanticMeans)),
      lexical_mean: round(mean(lexicalMeans)),
      lexical_var: round(variance(lexicalMeans)),
      mean_disagreement: round(mean(disagreementMeans)),
      disagreement_rate: round(disagreementRate),
      semantic_top1_share: round(topSemanticShare),
    },
    disagreement_buckets: buckets,
    clusters: clusters.sort((a, b) => a.clusterId.localeCompare(b.clusterId)),
  };

  const sampled = includeSample
    ? [...sample]
        .sort((a, b) => {
          if (b.disagreement !== a.disagreement) return b.disagreement - a.disagreement;
          if (a.clusterId !== b.clusterId) return a.clusterId.localeCompare(b.clusterId);
          if (a.aId !== b.aId) return a.aId.localeCompare(b.aId);
          return a.bId.localeCompare(b.bId);
        })
        .slice(0, sampleSize)
    : [];

  return {
    telemetry,
    sample: sampled,
  };
}

function sortByTimestamp<T extends { timestamp: number }>(a: T, b: T): number {
  if (a.timestamp !== b.timestamp) return a.timestamp - b.timestamp;
  return 0;
}

function emptyWindow(): RotationShadowWindowAggregate {
  return {
    count: 0,
    spanDays: 0,
    avg: emptyStats(),
  };
}

function aggregate(records: Array<{ timestamp: number; shadow?: RotationShadowTelemetry }>): RotationShadowWindowAggregate {
  const withShadow = records.filter((record) => Boolean(record.shadow));
  if (withShadow.length === 0) return emptyWindow();
  const sorted = [...withShadow].sort(sortByTimestamp);
  const count = sorted.length;
  const lexicalValues = sorted.map((record) => record.shadow!.semantic_stats.lexical_mean);
  const semanticValues = sorted.map((record) => record.shadow!.semantic_stats.semantic_mean);
  const disagreementValues = sorted.map((record) => record.shadow!.semantic_stats.mean_disagreement);
  const disagreementRateValues = sorted.map((record) => record.shadow!.semantic_stats.disagreement_rate);
  const topShareValues = sorted.map((record) => record.shadow!.semantic_stats.semantic_top1_share);
  return {
    count,
    spanDays: round((sorted[sorted.length - 1].timestamp - sorted[0].timestamp) / MS_PER_DAY, 3),
    avg: {
      lexical_mean: round(mean(lexicalValues)),
      lexical_var: round(mean(sorted.map((record) => record.shadow!.semantic_stats.lexical_var))),
      semantic_mean: round(mean(semanticValues)),
      semantic_var: round(mean(sorted.map((record) => record.shadow!.semantic_stats.semantic_var))),
      mean_disagreement: round(mean(disagreementValues)),
      disagreement_rate: round(mean(disagreementRateValues)),
      semantic_top1_share: round(mean(topShareValues)),
    },
  };
}

function ewma(records: Array<{ timestamp: number; shadow?: RotationShadowTelemetry }>): RotationShadowSemanticStats {
  const withShadow = records.filter((record) => Boolean(record.shadow)).sort(sortByTimestamp);
  if (withShadow.length === 0) return emptyStats();
  const first = withShadow[0].shadow!.semantic_stats;
  const acc = { ...first };
  for (let i = 1; i < withShadow.length; i++) {
    const current = withShadow[i].shadow!.semantic_stats;
    acc.lexical_mean = EWMA_ALPHA * current.lexical_mean + (1 - EWMA_ALPHA) * acc.lexical_mean;
    acc.lexical_var = EWMA_ALPHA * current.lexical_var + (1 - EWMA_ALPHA) * acc.lexical_var;
    acc.semantic_mean = EWMA_ALPHA * current.semantic_mean + (1 - EWMA_ALPHA) * acc.semantic_mean;
    acc.semantic_var = EWMA_ALPHA * current.semantic_var + (1 - EWMA_ALPHA) * acc.semantic_var;
    acc.mean_disagreement =
      EWMA_ALPHA * current.mean_disagreement + (1 - EWMA_ALPHA) * acc.mean_disagreement;
    acc.disagreement_rate =
      EWMA_ALPHA * current.disagreement_rate + (1 - EWMA_ALPHA) * acc.disagreement_rate;
    acc.semantic_top1_share =
      EWMA_ALPHA * current.semantic_top1_share + (1 - EWMA_ALPHA) * acc.semantic_top1_share;
  }
  return {
    lexical_mean: round(acc.lexical_mean),
    lexical_var: round(acc.lexical_var),
    semantic_mean: round(acc.semantic_mean),
    semantic_var: round(acc.semantic_var),
    mean_disagreement: round(acc.mean_disagreement),
    disagreement_rate: round(acc.disagreement_rate),
    semantic_top1_share: round(acc.semantic_top1_share),
  };
}

export function summarizeRotationShadowTelemetry(
  records: Array<{ timestamp: number; shadow?: RotationShadowTelemetry }>,
  now = Date.now(),
): RotationShadowTelemetrySummary {
  const withShadow = records.filter((record) => Boolean(record.shadow)).sort(sortByTimestamp);
  const latestTimestamp = withShadow.length > 0 ? withShadow[withShadow.length - 1].timestamp : 0;
  const latestModel = withShadow.length > 0 ? withShadow[withShadow.length - 1].shadow!.embeddingModel : null;
  const counts = emptyBuckets();
  for (const record of withShadow) {
    const buckets = record.shadow!.disagreement_buckets;
    for (const key of Object.keys(counts) as ShadowDisagreementBucket[]) {
      counts[key] += buckets[key] || 0;
    }
  }
  return {
    totalRuns: withShadow.length,
    latestTimestamp,
    embeddingModel: latestModel,
    ewma: ewma(withShadow),
    disagreement_buckets: counts,
    runWindows: {
      "10r": aggregate(withShadow.slice(-10)),
      "30r": aggregate(withShadow.slice(-30)),
      "90r": aggregate(withShadow.slice(-90)),
    },
    timeWindows: {
      "7d": aggregate(withShadow.filter((record) => record.timestamp >= now - 7 * MS_PER_DAY)),
      "30d": aggregate(withShadow.filter((record) => record.timestamp >= now - 30 * MS_PER_DAY)),
      "90d": aggregate(withShadow.filter((record) => record.timestamp >= now - 90 * MS_PER_DAY)),
    },
  };
}
