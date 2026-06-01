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
// Spiral-Level: High - this file enforces persistence-level memory orbit.
import { createHash } from "crypto";
import type { Memory } from "@shared/schema";
import { tokenizeForMemoryScoring } from "./memory-scoring";

const MS_PER_DAY = 1000 * 60 * 60 * 24;

export interface MemoryRotationPolicy {
  enabled: boolean;
  clusterSimilarityThreshold: number;
  mergeSimilarityThreshold: number;
  rotationHysteresis: number;
  activeSlotsPerCluster: number;
  maxActivePerGroup: number;
  recencyHalfLifeDays: number;
  reactivationWindowDays: number;
  driftPenaltyWeight: number;
  mergeConfidenceGain: number;
  mergeResurfaceGain: number;
}

export type MemoryRotationReason =
  | "SIM_DUPLICATE"
  | "ROTATE_HYSTERESIS_TRIGGER"
  | "ROTATE_HYSTERESIS_HOLD"
  | "CAP_DEMOTION"
  | "QUIET_GUARD_BLOCK"
  | "SINGLETON_PROMOTED_TO_ACTIVE"
  | "MERGE_REP_CHOSEN_BY_SCORE"
  | "MERGE_REP_CHOSEN_BY_RECENCY"
  | "DRIFT_PENALTY_HIGH";

export interface MemoryRotationAction {
  type:
    | "merge"
    | "rotate"
    | "hysteresis-hold"
    | "promote"
    | "demote"
    | "guard-block"
    | "merge-representative";
  reason: MemoryRotationReason;
  from?: string | string[];
  to?: string;
  memoryId?: string;
  detail?: string;
}

export interface MemoryClusterSnapshot {
  representativeId?: string;
  memberIds: string[];
  activeIds: string[];
  quietIds: string[];
  size: number;
}

export interface MemoryRotationSignals {
  similarity: number;
  hysteresis:
    | {
        incumbentId?: string;
        challengerId?: string;
        incumbentScore: number;
        challengerScore: number;
        triggerThreshold: number;
        triggered: boolean;
      }
    | null;
  cap: number;
  topFeatures: string[];
}

export interface MemoryRotationClusterReport {
  clusterId: string;
  groupKey: string;
  changed: boolean;
  before: MemoryClusterSnapshot;
  after: MemoryClusterSnapshot;
  actions: MemoryRotationAction[];
  signals: MemoryRotationSignals;
  scores: Record<string, number>;
}

export interface MemoryRotationStats {
  totalBefore: number;
  totalAfter: number;
  clusterCount: number;
  changedClusterCount: number;
  mergedCount: number;
  deletedCount: number;
  rotatedCount: number;
  promotedCount: number;
  demotedCount: number;
  capacityDemotedCount: number;
  quietGuardBlockedCount: number;
}

export interface MemoryRotationResult {
  memories: Memory[];
  changed: boolean;
  stats: MemoryRotationStats;
  clusters: MemoryRotationClusterReport[];
}

interface ClusterMember {
  memory: Memory;
  tokens: Set<string>;
}

interface ClusterScore {
  member: ClusterMember;
  score: number;
  driftPenalty: number;
}

interface ClusterRuntime {
  report: MemoryRotationClusterReport;
  afterIds: Set<string>;
}

const IMPORT_SUMMARY_CANONICAL_SOURCES = new Set([
  "import-summary",
  "system-summary",
  "manual-demoted-anchor",
]);
const IMPORT_SUMMARY_METADATA_PREFIX = /^imported history includes\b/i;
const IMPORT_SUMMARY_FOCUS_PREFIX = /^recent technical focus includes\b/i;
const IMPORT_SUMMARY_TARGET_PREFIX = /^current work targets\b/i;
const IMPORT_SUMMARY_QUESTION_PREFIX = /^open questions include\b/i;

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function parsePositiveNumber(value: string | undefined, fallback: number): number {
  const parsed = Number.parseFloat(value || "");
  if (Number.isFinite(parsed) && parsed > 0) {
    return parsed;
  }
  return fallback;
}

function parsePositiveInteger(value: string | undefined, fallback: number): number {
  const parsed = Number.parseInt(value || "", 10);
  if (Number.isFinite(parsed) && parsed > 0) {
    return parsed;
  }
  return fallback;
}

function parseBoolean(value: string | undefined, fallback: boolean): boolean {
  if (typeof value !== "string") return fallback;
  const normalized = value.trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) return true;
  if (["0", "false", "no", "off"].includes(normalized)) return false;
  return fallback;
}

function memoryGroupKey(memory: Memory): string {
  return `${memory.principalId || ""}::${memory.domain}`;
}

function sortIds(values: string[]): string[] {
  return [...values].sort((a, b) => a.localeCompare(b));
}

function stableClusterId(groupKey: string, memberIds: string[]): string {
  return createHash("sha1")
    .update(groupKey)
    .update("::")
    .update(sortIds(memberIds).join("|"))
    .digest("hex")
    .slice(0, 12);
}

function memorySortDesc(a: Memory, b: Memory): number {
  if (b.lastUsedAt !== a.lastUsedAt) return b.lastUsedAt - a.lastUsedAt;
  if (b.updatedAt !== a.updatedAt) return b.updatedAt - a.updatedAt;
  return a.id.localeCompare(b.id);
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
  return Math.max(jaccard, containment * 0.92);
}

function canonicalizeImportSummaryContent(content: string): string {
  const normalized = content.replace(/\s+/g, " ").trim();
  if (!normalized) return normalized;
  const sentences = normalized
    .split(/(?<=[.!?])\s+/g)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
  if (sentences.length === 0) return normalized;

  const transformed: string[] = [];
  for (const sentence of sentences) {
    if (IMPORT_SUMMARY_METADATA_PREFIX.test(sentence)) {
      continue;
    }
    let current = sentence;
    if (IMPORT_SUMMARY_FOCUS_PREFIX.test(current)) {
      current = current.replace(IMPORT_SUMMARY_FOCUS_PREFIX, "").trim();
    } else if (IMPORT_SUMMARY_TARGET_PREFIX.test(current)) {
      current = current.replace(IMPORT_SUMMARY_TARGET_PREFIX, "").trim();
    } else if (IMPORT_SUMMARY_QUESTION_PREFIX.test(current)) {
      current = current.replace(IMPORT_SUMMARY_QUESTION_PREFIX, "").trim();
    }
    current = current.replace(/^[:\-\s]+/, "").trim();
    if (current) {
      transformed.push(current);
    }
  }

  if (transformed.length === 0) {
    return normalized;
  }
  return transformed.join(" ");
}

function contentForClustering(memory: Memory): string {
  const source = (memory.source || "").trim().toLowerCase();
  if (!IMPORT_SUMMARY_CANONICAL_SOURCES.has(source)) {
    return memory.content;
  }
  return canonicalizeImportSummaryContent(memory.content);
}

export function tokenizeMemoryForRotation(memory: Memory): Set<string> {
  return tokenizeForMemoryScoring(contentForClustering(memory));
}

function clusterSimilarity(candidateTokens: Set<string>, members: ClusterMember[]): number {
  if (candidateTokens.size === 0 || members.length === 0) return 0;
  let maxSimilarity = 0;
  let totalSimilarity = 0;
  for (const member of members) {
    const similarity = setSimilarity(candidateTokens, member.tokens);
    totalSimilarity += similarity;
    if (similarity > maxSimilarity) {
      maxSimilarity = similarity;
    }
  }
  const averageSimilarity = totalSimilarity / members.length;
  return Math.max(maxSimilarity, averageSimilarity * 0.9);
}

function recencySignal(lastUsedAt: number, now: number, halfLifeDays: number): number {
  const ageDays = Math.max(0, (now - lastUsedAt) / MS_PER_DAY);
  return Math.exp(-ageDays / Math.max(0.1, halfLifeDays));
}

function recurrenceSignal(resurfaceCount: number): number {
  return clamp(Math.log1p(Math.max(0, resurfaceCount)) / Math.log(10), 0, 1);
}

function confirmationSignal(memory: Memory): number {
  const unconfirmed = memory.requiresConfirmation && memory.lastConfirmedAt <= memory.createdAt;
  return unconfirmed ? 0.55 : 1;
}

function cohesionSignal(tokens: Set<string>, members: ClusterMember[]): number {
  if (members.length <= 1 || tokens.size === 0) return 1;
  let total = 0;
  let comparisons = 0;
  for (const member of members) {
    if (member.tokens === tokens) continue;
    total += setSimilarity(tokens, member.tokens);
    comparisons += 1;
  }
  if (comparisons === 0) return 1;
  return clamp(total / comparisons, 0, 1);
}

function computeMemberScore(
  member: ClusterMember,
  clusterMembers: ClusterMember[],
  now: number,
  policy: MemoryRotationPolicy,
): ClusterScore {
  const confidence = clamp(member.memory.confidenceScore, 0, 1);
  const freshness = recencySignal(member.memory.lastUsedAt, now, policy.recencyHalfLifeDays);
  const recurrence = recurrenceSignal(member.memory.resurfaceCount);
  const confirmation = confirmationSignal(member.memory);
  const cohesion = cohesionSignal(member.tokens, clusterMembers);
  const ageDays = Math.max(0, (now - member.memory.updatedAt) / MS_PER_DAY);
  const driftPenalty = clamp(
    1 - (1 - cohesion) * clamp(ageDays / 120, 0, 1) * clamp(policy.driftPenaltyWeight, 0, 1),
    0.35,
    1,
  );
  const base = confidence * 0.38 + freshness * 0.27 + recurrence * 0.13 + cohesion * 0.22;
  return {
    member,
    score: base * confirmation * driftPenalty,
    driftPenalty,
  };
}

function scoreClusterMembers(
  members: ClusterMember[],
  now: number,
  policy: MemoryRotationPolicy,
): ClusterScore[] {
  return members
    .map((member) => computeMemberScore(member, members, now, policy))
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return memorySortDesc(a.member.memory, b.member.memory);
    });
}

function buildClusters(members: ClusterMember[], threshold: number): ClusterMember[][] {
  const clusters: ClusterMember[][] = [];
  for (const member of members) {
    let bestIndex = -1;
    let bestSimilarity = 0;

    for (let i = 0; i < clusters.length; i++) {
      const similarity = clusterSimilarity(member.tokens, clusters[i]);
      if (similarity > bestSimilarity) {
        bestSimilarity = similarity;
        bestIndex = i;
      }
    }

    if (bestIndex >= 0 && bestSimilarity >= threshold) {
      clusters[bestIndex].push(member);
    } else {
      clusters.push([member]);
    }
  }

  return clusters;
}

function computeCapacityScore(memory: Memory, now: number, recencyHalfLifeDays: number): number {
  const confidence = clamp(memory.confidenceScore, 0, 1);
  const freshness = recencySignal(memory.lastUsedAt, now, recencyHalfLifeDays);
  const recurrence = recurrenceSignal(memory.resurfaceCount);
  const confirmation = confirmationSignal(memory);
  const base = confidence * 0.45 + freshness * 0.35 + recurrence * 0.2;
  return base * confirmation;
}

function isRecentlyTouched(memory: Memory, now: number, reactivationWindowDays: number): boolean {
  const ageDays = Math.max(0, (now - memory.lastUsedAt) / MS_PER_DAY);
  return ageDays <= Math.max(1, reactivationWindowDays);
}

function topClusterFeatures(members: ClusterMember[], limit = 6): string[] {
  const counts = new Map<string, number>();
  for (const member of members) {
    for (const token of Array.from(member.tokens)) {
      counts.set(token, (counts.get(token) || 0) + 1);
    }
  }
  return Array.from(counts.entries())
    .sort((a, b) => {
      if (b[1] !== a[1]) return b[1] - a[1];
      return a[0].localeCompare(b[0]);
    })
    .slice(0, limit)
    .map(([token]) => token);
}

function createSnapshot(
  memoryMap: Map<string, Memory>,
  memberIds: Iterable<string>,
  representativeId?: string,
): MemoryClusterSnapshot {
  const members = Array.from(memberIds)
    .map((id) => memoryMap.get(id))
    .filter((memory): memory is Memory => Boolean(memory))
    .sort(memorySortDesc);
  const ids = members.map((memory) => memory.id);
  const activeIds = members.filter((memory) => memory.status === "active").map((memory) => memory.id);
  const quietIds = members.filter((memory) => memory.status === "quiet").map((memory) => memory.id);

  let resolvedRepresentative = representativeId;
  if (resolvedRepresentative && !ids.includes(resolvedRepresentative)) {
    resolvedRepresentative = undefined;
  }
  if (!resolvedRepresentative) {
    resolvedRepresentative = activeIds[0] || ids[0];
  }

  return {
    representativeId: resolvedRepresentative,
    memberIds: ids,
    activeIds,
    quietIds,
    size: ids.length,
  };
}

function actionSortRank(type: MemoryRotationAction["type"]): number {
  switch (type) {
    case "rotate":
      return 0;
    case "hysteresis-hold":
      return 1;
    case "merge-representative":
      return 2;
    case "merge":
      return 3;
    case "promote":
      return 4;
    case "demote":
      return 5;
    case "guard-block":
      return 6;
  }
}

function normalizeActionEndpoint(value: string | string[] | undefined): string {
  if (!value) return "";
  if (Array.isArray(value)) {
    return sortIds(value).join("|");
  }
  return value;
}

function sortActions(actions: MemoryRotationAction[]): MemoryRotationAction[] {
  return [...actions].sort((a, b) => {
    const rank = actionSortRank(a.type) - actionSortRank(b.type);
    if (rank !== 0) return rank;
    if (a.reason !== b.reason) return a.reason.localeCompare(b.reason);
    const fromCompare = normalizeActionEndpoint(a.from).localeCompare(normalizeActionEndpoint(b.from));
    if (fromCompare !== 0) return fromCompare;
    const toCompare = (a.to || "").localeCompare(b.to || "");
    if (toCompare !== 0) return toCompare;
    return (a.memoryId || "").localeCompare(b.memoryId || "");
  });
}

function mergeRepresentative(
  representative: Memory,
  secondary: Memory[],
  scoresById: Map<string, number>,
  now: number,
  policy: MemoryRotationPolicy,
): Memory {
  if (secondary.length === 0) return representative;
  const bundle = [representative, ...secondary];
  let totalWeight = 0;
  let weightedConfidence = 0;
  let weightedIntent = 0;
  let weightedHalfLife = 0;
  let maxLastUsedAt = representative.lastUsedAt;
  let maxLastConfirmedAt = representative.lastConfirmedAt;
  let maxUpdatedAt = representative.updatedAt;
  let combinedResurfaceCount = representative.resurfaceCount;
  let confirmationPrompted = representative.confirmationPrompted;
  let requiresConfirmation = representative.requiresConfirmation;

  for (const memory of bundle) {
    const score = Math.max(0.05, scoresById.get(memory.id) || 0.1);
    totalWeight += score;
    weightedConfidence += clamp(memory.confidenceScore, 0, 1) * score;
    weightedIntent += clamp(memory.intentBias, -1, 1) * score;
    weightedHalfLife += Math.max(1, memory.halfLifeDays) * score;
    maxLastUsedAt = Math.max(maxLastUsedAt, memory.lastUsedAt);
    maxLastConfirmedAt = Math.max(maxLastConfirmedAt, memory.lastConfirmedAt);
    maxUpdatedAt = Math.max(maxUpdatedAt, memory.updatedAt);
    if (memory !== representative) {
      combinedResurfaceCount += memory.resurfaceCount;
    }
    confirmationPrompted = confirmationPrompted || memory.confirmationPrompted;
    requiresConfirmation = requiresConfirmation || memory.requiresConfirmation;
  }

  const confidenceTarget = totalWeight > 0 ? weightedConfidence / totalWeight : representative.confidenceScore;
  const intentTarget = totalWeight > 0 ? weightedIntent / totalWeight : representative.intentBias;
  const halfLifeTarget = totalWeight > 0 ? weightedHalfLife / totalWeight : representative.halfLifeDays;
  const confidenceScore = clamp(
    representative.confidenceScore +
      (confidenceTarget - representative.confidenceScore) * clamp(policy.mergeConfidenceGain, 0, 1),
    0,
    1,
  );
  const resurfaceBonus = Math.round(
    Math.max(0, combinedResurfaceCount - representative.resurfaceCount) *
      clamp(policy.mergeResurfaceGain, 0, 1),
  );

  return {
    ...representative,
    confidenceScore,
    intentBias: clamp(intentTarget, -1, 1),
    halfLifeDays: Math.max(1, halfLifeTarget),
    resurfaceCount: Math.max(
      representative.resurfaceCount + secondary.length,
      representative.resurfaceCount + resurfaceBonus,
    ),
    lastUsedAt: maxLastUsedAt,
    lastConfirmedAt: maxLastConfirmedAt,
    updatedAt: Math.max(now, maxUpdatedAt),
    confirmationPrompted,
    requiresConfirmation,
    status: "active",
  };
}

export function getMemoryRotationPolicy(env: NodeJS.ProcessEnv = process.env): MemoryRotationPolicy {
  return {
    enabled: parseBoolean(env.MEMORY_ROTATION_ENABLED, true),
    clusterSimilarityThreshold: clamp(
      parsePositiveNumber(env.MEMORY_ROTATION_CLUSTER_SIMILARITY, 0.63),
      0.35,
      0.95,
    ),
    mergeSimilarityThreshold: clamp(
      parsePositiveNumber(env.MEMORY_ROTATION_MERGE_SIMILARITY, 0.86),
      0.55,
      0.99,
    ),
    rotationHysteresis: clamp(
      parsePositiveNumber(env.MEMORY_ROTATION_HYSTERESIS, 0.08),
      0.01,
      0.5,
    ),
    activeSlotsPerCluster: Math.max(1, parsePositiveInteger(env.MEMORY_ROTATION_ACTIVE_SLOTS, 1)),
    maxActivePerGroup: Math.max(4, parsePositiveInteger(env.MEMORY_ROTATION_MAX_ACTIVE_PER_GROUP, 96)),
    recencyHalfLifeDays: Math.max(1, parsePositiveNumber(env.MEMORY_ROTATION_RECENCY_HALF_LIFE_DAYS, 21)),
    reactivationWindowDays: Math.max(
      1,
      parsePositiveNumber(env.MEMORY_ROTATION_REACTIVATION_WINDOW_DAYS, 10),
    ),
    driftPenaltyWeight: clamp(parsePositiveNumber(env.MEMORY_ROTATION_DRIFT_WEIGHT, 0.45), 0.05, 1),
    mergeConfidenceGain: clamp(parsePositiveNumber(env.MEMORY_ROTATION_MERGE_CONFIDENCE_GAIN, 0.35), 0.05, 1),
    mergeResurfaceGain: clamp(parsePositiveNumber(env.MEMORY_ROTATION_MERGE_RESURFACE_GAIN, 0.45), 0.05, 1),
  };
}

export function applyRotationalMemoryPruning(
  memories: Memory[],
  policy = getMemoryRotationPolicy(),
  now = Date.now(),
): MemoryRotationResult {
  const stats: MemoryRotationStats = {
    totalBefore: memories.length,
    totalAfter: memories.length,
    clusterCount: 0,
    changedClusterCount: 0,
    mergedCount: 0,
    deletedCount: 0,
    rotatedCount: 0,
    promotedCount: 0,
    demotedCount: 0,
    capacityDemotedCount: 0,
    quietGuardBlockedCount: 0,
  };
  if (!policy.enabled || memories.length === 0) {
    return {
      memories,
      changed: false,
      stats,
      clusters: [],
    };
  }

  const nextMemories = new Map<string, Memory>();
  for (const memory of memories) {
    nextMemories.set(memory.id, { ...memory });
  }
  let changed = false;

  const eligibleByGroup = new Map<string, ClusterMember[]>();
  for (const memory of Array.from(nextMemories.values())) {
    if (memory.status === "released") continue;
    if (memory.memoryType === "anchor") continue;
    const key = memoryGroupKey(memory);
    const tokens = tokenizeMemoryForRotation(memory);
    const members = eligibleByGroup.get(key);
    const entry: ClusterMember = { memory, tokens };
    if (members) {
      members.push(entry);
    } else {
      eligibleByGroup.set(key, [entry]);
    }
  }

  const runtimes: ClusterRuntime[] = [];

  for (const [groupKey, members] of Array.from(eligibleByGroup.entries()).sort((a, b) => a[0].localeCompare(b[0]))) {
    if (members.length === 0) continue;
    members.sort((a, b) => memorySortDesc(a.memory, b.memory));
    const clusters = buildClusters(members, policy.clusterSimilarityThreshold);
    stats.clusterCount += clusters.length;

    for (const cluster of clusters) {
      if (cluster.length === 0) continue;
      const beforeIds = sortIds(cluster.map((entry) => entry.memory.id));
      const clusterId = stableClusterId(groupKey, beforeIds);
      const ranked = scoreClusterMembers(cluster, now, policy);
      const scoreMap = new Map<string, number>(ranked.map((item) => [item.member.memory.id, item.score]));
      const scoresObject: Record<string, number> = {};
      for (const item of ranked) {
        scoresObject[item.member.memory.id] = Number(item.score.toFixed(6));
      }

      const incumbent = ranked.find((item) => item.member.memory.status === "active");
      const top = ranked[0];
      let representative = top;
      let repChoiceReason: MemoryRotationReason = "MERGE_REP_CHOSEN_BY_SCORE";
      let hysteresisSignal: MemoryRotationSignals["hysteresis"] = null;
      const actions: MemoryRotationAction[] = [];

      if (incumbent && incumbent.member.memory.id !== top.member.memory.id) {
        const triggerThreshold = incumbent.score * (1 + policy.rotationHysteresis);
        const shouldRotate = top.score >= triggerThreshold;
        hysteresisSignal = {
          incumbentId: incumbent.member.memory.id,
          challengerId: top.member.memory.id,
          incumbentScore: Number(incumbent.score.toFixed(6)),
          challengerScore: Number(top.score.toFixed(6)),
          triggerThreshold: Number(triggerThreshold.toFixed(6)),
          triggered: shouldRotate,
        };
        if (shouldRotate) {
          stats.rotatedCount += 1;
          representative = top;
          actions.push({
            type: "rotate",
            reason: "ROTATE_HYSTERESIS_TRIGGER",
            from: incumbent.member.memory.id,
            to: top.member.memory.id,
            detail: `${top.score.toFixed(3)} >= ${triggerThreshold.toFixed(3)}`,
          });
          repChoiceReason = "MERGE_REP_CHOSEN_BY_SCORE";
        } else {
          representative = incumbent;
          repChoiceReason = "MERGE_REP_CHOSEN_BY_RECENCY";
          actions.push({
            type: "hysteresis-hold",
            reason: "ROTATE_HYSTERESIS_HOLD",
            from: top.member.memory.id,
            to: incumbent.member.memory.id,
            detail: `${top.score.toFixed(3)} < ${triggerThreshold.toFixed(3)}`,
          });
        }
      }

      const mergeThreshold = Math.max(policy.clusterSimilarityThreshold, policy.mergeSimilarityThreshold);
      const representativeTokens = representative.member.tokens;
      const secondaryToMerge = ranked
        .filter((item) => item.member.memory.id !== representative.member.memory.id)
        .filter((item) => setSimilarity(item.member.tokens, representativeTokens) >= mergeThreshold);

      if (secondaryToMerge.length > 0) {
        actions.push({
          type: "merge-representative",
          reason: repChoiceReason,
          to: representative.member.memory.id,
        });

        const representativeMemory =
          nextMemories.get(representative.member.memory.id) || representative.member.memory;
        const merged = mergeRepresentative(
          representativeMemory,
          secondaryToMerge.map((item) => nextMemories.get(item.member.memory.id) || item.member.memory),
          scoreMap,
          now,
          policy,
        );
        nextMemories.set(merged.id, merged);
        changed = true;

        const mergedIds: string[] = [];
        for (const item of secondaryToMerge) {
          if (nextMemories.delete(item.member.memory.id)) {
            mergedIds.push(item.member.memory.id);
            stats.mergedCount += 1;
            stats.deletedCount += 1;
            changed = true;
          }
        }
        if (mergedIds.length > 0) {
          actions.push({
            type: "merge",
            reason: "SIM_DUPLICATE",
            from: sortIds(mergedIds),
            to: merged.id,
            detail: `similarity>=${mergeThreshold.toFixed(2)}`,
          });
        }
      }

      const afterIds = new Set(beforeIds.filter((id) => nextMemories.has(id)));
      const remainingMembers = Array.from(afterIds)
        .map((id) => nextMemories.get(id))
        .filter((memory): memory is Memory => Boolean(memory))
        .map((memory) => ({
          memory,
          tokens: tokenizeMemoryForRotation(memory),
        }));

      const remainingRanked = scoreClusterMembers(remainingMembers, now, policy);
      const remainingById = new Map(remainingRanked.map((item) => [item.member.memory.id, item]));
      const representativeId = nextMemories.has(representative.member.memory.id)
        ? representative.member.memory.id
        : remainingRanked[0]?.member.memory.id;
      const preferredRepresentative =
        representativeId && remainingById.has(representativeId)
          ? remainingById.get(representativeId)!
          : remainingRanked[0];
      const ordered = preferredRepresentative
        ? [
            preferredRepresentative,
            ...remainingRanked.filter((item) => item.member.memory.id !== preferredRepresentative.member.memory.id),
          ]
        : remainingRanked;

      const activeLimit = Math.max(1, policy.activeSlotsPerCluster);
      const clusterHasActive = remainingRanked.some((item) => item.member.memory.status === "active");
      for (let index = 0; index < ordered.length; index++) {
        const scored = ordered[index];
        const memory = nextMemories.get(scored.member.memory.id);
        if (!memory) continue;
        let targetStatus: Memory["status"] = index < activeLimit ? "active" : "quiet";
        if (
          targetStatus === "active" &&
          memory.status !== "active" &&
          !clusterHasActive &&
          !isRecentlyTouched(memory, now, policy.reactivationWindowDays)
        ) {
          targetStatus = memory.status;
          stats.quietGuardBlockedCount += 1;
          actions.push({
            type: "guard-block",
            reason: "QUIET_GUARD_BLOCK",
            memoryId: memory.id,
            detail: `lastUsed>${policy.reactivationWindowDays}d`,
          });
        }

        if (memory.status !== targetStatus) {
          if (targetStatus === "active") {
            stats.promotedCount += 1;
            const promoteReason: MemoryRotationReason =
              ordered.length <= 1
                ? "SINGLETON_PROMOTED_TO_ACTIVE"
                : preferredRepresentative && memory.id === preferredRepresentative.member.memory.id
                  ? repChoiceReason
                  : "MERGE_REP_CHOSEN_BY_SCORE";
            actions.push({
              type: "promote",
              reason: promoteReason,
              memoryId: memory.id,
            });
          } else {
            stats.demotedCount += 1;
            actions.push({
              type: "demote",
              reason: scored.driftPenalty < 0.58 ? "DRIFT_PENALTY_HIGH" : "CAP_DEMOTION",
              memoryId: memory.id,
              detail: `slot>${activeLimit}`,
            });
          }

          nextMemories.set(memory.id, {
            ...memory,
            status: targetStatus,
            updatedAt: Math.max(memory.updatedAt, now),
          });
          changed = true;
        }
      }

      const similarityCandidates = remainingRanked
        .filter((item) => item.member.memory.id !== (preferredRepresentative?.member.memory.id || ""))
        .map((item) =>
          setSimilarity(
            item.member.tokens,
            preferredRepresentative?.member.tokens || new Set<string>(),
          ),
        );
      const similaritySignal =
        similarityCandidates.length > 0
          ? Number(Math.max(...similarityCandidates).toFixed(6))
          : 0;
      const report: MemoryRotationClusterReport = {
        clusterId,
        groupKey,
        changed: false,
        before: createSnapshot(
          new Map(cluster.map((entry) => [entry.memory.id, entry.memory])),
          beforeIds,
          incumbent?.member.memory.id || top.member.memory.id,
        ),
        after: createSnapshot(nextMemories, afterIds, preferredRepresentative?.member.memory.id),
        actions: sortActions(actions),
        signals: {
          similarity: similaritySignal,
          hysteresis: hysteresisSignal,
          cap: policy.maxActivePerGroup,
          topFeatures: topClusterFeatures(cluster),
        },
        scores: scoresObject,
      };
      report.changed =
        report.actions.length > 0 ||
        report.before.representativeId !== report.after.representativeId ||
        report.before.memberIds.join("|") !== report.after.memberIds.join("|") ||
        report.before.activeIds.join("|") !== report.after.activeIds.join("|");
      if (report.changed) {
        stats.changedClusterCount += 1;
      }

      runtimes.push({
        report,
        afterIds,
      });
    }
  }

  const memoryToRuntime = new Map<string, ClusterRuntime>();
  for (const runtime of runtimes) {
    for (const id of Array.from(runtime.afterIds)) {
      memoryToRuntime.set(id, runtime);
    }
  }

  for (const groupKey of Array.from(eligibleByGroup.keys()).sort((a, b) => a.localeCompare(b))) {
    const activeCandidates = Array.from(nextMemories.values())
      .filter((memory) => memory.status === "active")
      .filter((memory) => memory.memoryType !== "anchor")
      .filter((memory) => memory.status !== "released")
      .filter((memory) => memoryGroupKey(memory) === groupKey)
      .sort((a, b) => {
        const scoreA = computeCapacityScore(a, now, policy.recencyHalfLifeDays);
        const scoreB = computeCapacityScore(b, now, policy.recencyHalfLifeDays);
        if (scoreA !== scoreB) return scoreA - scoreB;
        return memorySortDesc(a, b) * -1;
      });

    if (activeCandidates.length <= policy.maxActivePerGroup) continue;
    const overflow = activeCandidates.length - policy.maxActivePerGroup;
    for (const memory of activeCandidates.slice(0, overflow)) {
      const current = nextMemories.get(memory.id);
      if (!current || current.status !== "active") continue;
      nextMemories.set(memory.id, {
        ...current,
        status: "quiet",
        updatedAt: Math.max(current.updatedAt, now),
      });
      stats.capacityDemotedCount += 1;
      stats.demotedCount += 1;
      changed = true;
      const runtime = memoryToRuntime.get(memory.id);
      if (runtime) {
        runtime.report.actions = sortActions([
          ...runtime.report.actions,
          {
            type: "demote",
            reason: "CAP_DEMOTION",
            memoryId: memory.id,
            detail: `groupActive>${policy.maxActivePerGroup}`,
          },
        ]);
      }
    }
  }

  for (const runtime of runtimes) {
    runtime.report.after = createSnapshot(
      nextMemories,
      runtime.afterIds,
      runtime.report.after.representativeId,
    );
    runtime.report.changed =
      runtime.report.actions.length > 0 ||
      runtime.report.before.representativeId !== runtime.report.after.representativeId ||
      runtime.report.before.memberIds.join("|") !== runtime.report.after.memberIds.join("|") ||
      runtime.report.before.activeIds.join("|") !== runtime.report.after.activeIds.join("|");
  }

  stats.changedClusterCount = runtimes.filter((runtime) => runtime.report.changed).length;
  stats.totalAfter = nextMemories.size;

  return {
    memories: Array.from(nextMemories.values()),
    changed,
    stats,
    clusters: [...runtimes.map((runtime) => runtime.report)].sort((a, b) => {
      if (a.groupKey !== b.groupKey) return a.groupKey.localeCompare(b.groupKey);
      return a.clusterId.localeCompare(b.clusterId);
    }),
  };
}
