import assert from "node:assert/strict";
import test from "node:test";
import type { Memory } from "../shared/schema";
import {
  applyRotationalMemoryPruning,
  type MemoryRotationPolicy,
} from "../server/memory-rotation";

const DAY_MS = 24 * 60 * 60 * 1000;
const NOW = Date.UTC(2026, 0, 20);

function buildMemory(overrides: Partial<Memory> = {}): Memory {
  return {
    id: overrides.id ?? `m-${Math.random().toString(36).slice(2, 10)}`,
    content: overrides.content ?? "default memory line",
    principalId: overrides.principalId ?? "test:principal",
    memoryType: overrides.memoryType ?? "observation",
    source: overrides.source ?? "live",
    confidenceScore: overrides.confidenceScore ?? 0.7,
    status: overrides.status ?? "active",
    domain: overrides.domain ?? "operational",
    createdAt: overrides.createdAt ?? NOW - 90 * DAY_MS,
    updatedAt: overrides.updatedAt ?? NOW - 2 * DAY_MS,
    lastUsedAt: overrides.lastUsedAt ?? NOW - 2 * DAY_MS,
    lastConfirmedAt: overrides.lastConfirmedAt ?? NOW - 90 * DAY_MS,
    halfLifeDays: overrides.halfLifeDays ?? 45,
    requiresConfirmation: overrides.requiresConfirmation ?? false,
    intentBias: overrides.intentBias ?? -0.3,
    confirmationPrompted: overrides.confirmationPrompted ?? false,
    resurfaceCount: overrides.resurfaceCount ?? 0,
  };
}

function policy(overrides: Partial<MemoryRotationPolicy> = {}): MemoryRotationPolicy {
  return {
    enabled: true,
    clusterSimilarityThreshold: 0.6,
    mergeSimilarityThreshold: 0.86,
    rotationHysteresis: 0.08,
    activeSlotsPerCluster: 1,
    maxActivePerGroup: 32,
    recencyHalfLifeDays: 21,
    reactivationWindowDays: 10,
    driftPenaltyWeight: 0.45,
    mergeConfidenceGain: 0.35,
    mergeResurfaceGain: 0.45,
    ...overrides,
  };
}

test("rotational pruning merges near-duplicate memories at persistence layer", () => {
  const memories = [
    buildMemory({
      id: "dup-a",
      content: "release pipeline deployment checklist",
      confidenceScore: 0.72,
      lastUsedAt: NOW - 16 * DAY_MS,
      resurfaceCount: 4,
    }),
    buildMemory({
      id: "dup-b",
      content: "deployment checklist for release pipeline",
      confidenceScore: 0.76,
      lastUsedAt: NOW - 2 * DAY_MS,
      resurfaceCount: 2,
    }),
    buildMemory({
      id: "distinct",
      content: "observability dashboards for customer incidents",
      confidenceScore: 0.69,
      lastUsedAt: NOW - 2 * DAY_MS,
    }),
  ];

  const result = applyRotationalMemoryPruning(
    memories,
    policy({ mergeSimilarityThreshold: 0.82 }),
    NOW,
  );

  assert.equal(result.changed, true);
  const duplicateCount = result.memories.filter((memory) => /^dup-/.test(memory.id)).length;
  assert.equal(duplicateCount, 1, "Expected duplicate fragments to collapse into one representative.");
  assert.ok(result.stats.mergedCount >= 1, "Expected merge count to increase.");
  assert.ok(result.stats.deletedCount >= 1, "Expected merged secondary memory to be removed.");
});

test("rotational pruning can rotate active representative when theme drift occurs", () => {
  const memories = [
    buildMemory({
      id: "incumbent",
      content: "deployment pipeline release checklist",
      status: "active",
      confidenceScore: 0.95,
      lastUsedAt: NOW - 140 * DAY_MS,
      updatedAt: NOW - 130 * DAY_MS,
      resurfaceCount: 6,
    }),
    buildMemory({
      id: "challenger",
      content: "deployment pipeline for blue green rollout",
      status: "quiet",
      confidenceScore: 0.77,
      lastUsedAt: NOW - DAY_MS,
      updatedAt: NOW - DAY_MS,
      resurfaceCount: 1,
    }),
  ];

  const result = applyRotationalMemoryPruning(
    memories,
    policy({
      clusterSimilarityThreshold: 0.42,
      mergeSimilarityThreshold: 0.98,
      rotationHysteresis: 0.05,
    }),
    NOW,
  );
  const byId = new Map(result.memories.map((memory) => [memory.id, memory]));
  const incumbent = byId.get("incumbent");
  const challenger = byId.get("challenger");
  assert.ok(incumbent && challenger, "Expected both memories to remain after rotation.");
  assert.equal(challenger.status, "active", "Recent thematic challenger should become active representative.");
  assert.equal(incumbent.status, "quiet", "Stale incumbent should be rotated out to quiet.");
  assert.ok(result.stats.rotatedCount >= 1, "Expected representative rotation statistic to increment.");
});

test("rotational pruning demotes overflow when active memory exceeds per-group cap", () => {
  const memories = [
    buildMemory({
      id: "m-1",
      content: "infrastructure budget planning q1",
      lastUsedAt: NOW - DAY_MS,
      confidenceScore: 0.75,
    }),
    buildMemory({
      id: "m-2",
      content: "customer onboarding journey mapping",
      lastUsedAt: NOW - 2 * DAY_MS,
      confidenceScore: 0.72,
    }),
    buildMemory({
      id: "m-3",
      content: "incident response checklist updates",
      lastUsedAt: NOW - 6 * DAY_MS,
      confidenceScore: 0.7,
    }),
    buildMemory({
      id: "m-4",
      content: "roadmap prioritization for integrations",
      lastUsedAt: NOW - 10 * DAY_MS,
      confidenceScore: 0.68,
    }),
  ];

  const result = applyRotationalMemoryPruning(
    memories,
    policy({
      clusterSimilarityThreshold: 0.95,
      maxActivePerGroup: 2,
    }),
    NOW,
  );
  const activeCount = result.memories.filter((memory) => memory.status === "active").length;
  assert.equal(activeCount, 2, "Expected active memories to be capped at maxActivePerGroup.");
  assert.equal(result.stats.capacityDemotedCount, 2);
});

test("rotational pruning does not reactivate stale quiet singleton themes", () => {
  const quietMemory = buildMemory({
    id: "quiet-singleton",
    content: "legacy migration notes for archived service",
    status: "quiet",
    lastUsedAt: NOW - 120 * DAY_MS,
    updatedAt: NOW - 90 * DAY_MS,
  });

  const result = applyRotationalMemoryPruning(
    [quietMemory],
    policy({ reactivationWindowDays: 7 }),
    NOW,
  );
  const current = result.memories.find((memory) => memory.id === "quiet-singleton");
  assert.ok(current, "Expected singleton memory to remain present.");
  assert.equal(current.status, "quiet");
  assert.equal(result.stats.promotedCount, 0);
});

test("rotational pruning uses singleton promotion reason for quiet->active transition", () => {
  const quietMemory = buildMemory({
    id: "singleton-promote",
    content: "fresh singleton memory for quick promotion",
    status: "quiet",
    lastUsedAt: NOW - DAY_MS,
    updatedAt: NOW - DAY_MS,
  });

  const result = applyRotationalMemoryPruning(
    [quietMemory],
    policy({ reactivationWindowDays: 10 }),
    NOW,
  );
  const current = result.memories.find((memory) => memory.id === "singleton-promote");
  assert.ok(current, "Expected singleton memory to remain present.");
  assert.equal(current.status, "active");
  assert.equal(result.stats.promotedCount, 1);
  const promoteActions = result.clusters.flatMap((cluster) =>
    cluster.actions.filter((action) => action.type === "promote"),
  );
  assert.ok(promoteActions.length >= 1);
  assert.ok(
    promoteActions.some((action) => action.reason === "SINGLETON_PROMOTED_TO_ACTIVE"),
    "Expected singleton promotion reason for quiet->active transition.",
  );
});

test("import-summary canonicalization prevents boilerplate-only clustering", () => {
  const memories = [
    buildMemory({
      id: "import-a",
      source: "import-summary",
      content:
        "Imported history includes 200 conversations and 8000 messages. Recent technical focus includes onion, skillet, olive. Current work targets caramelize onions for dinner. Open questions include Should heat be medium.",
      status: "active",
      confidenceScore: 0.74,
      lastUsedAt: NOW - DAY_MS,
    }),
    buildMemory({
      id: "import-b",
      source: "import-summary",
      content:
        "Imported history includes 200 conversations and 7000 messages. Recent technical focus includes kubernetes, ingress, rollout. Current work targets patch envoy timeout settings. Open questions include Which service owns retries.",
      status: "active",
      confidenceScore: 0.73,
      lastUsedAt: NOW - DAY_MS,
    }),
  ];

  const result = applyRotationalMemoryPruning(
    memories,
    policy({
      clusterSimilarityThreshold: 0.6,
      mergeSimilarityThreshold: 0.95,
    }),
    NOW,
  );

  assert.equal(
    result.stats.clusterCount,
    2,
    "Expected import-summary memories with different payloads to avoid boilerplate-driven clustering.",
  );
});

test("rotational pruning reports deterministic cluster/action ordering", () => {
  const input = [
    buildMemory({
      id: "a-memory",
      content: "release pipeline checklist",
      confidenceScore: 0.82,
      lastUsedAt: NOW - 30 * DAY_MS,
      status: "active",
    }),
    buildMemory({
      id: "b-memory",
      content: "pipeline release deployment checklist",
      confidenceScore: 0.79,
      lastUsedAt: NOW - 2 * DAY_MS,
      status: "quiet",
    }),
    buildMemory({
      id: "c-memory",
      content: "database migration rollback protocol",
      confidenceScore: 0.72,
      lastUsedAt: NOW - 3 * DAY_MS,
      status: "active",
    }),
  ];

  const runOne = applyRotationalMemoryPruning(
    input,
    policy({
      clusterSimilarityThreshold: 0.5,
      mergeSimilarityThreshold: 0.82,
      rotationHysteresis: 0.06,
    }),
    NOW,
  );
  const runTwo = applyRotationalMemoryPruning(
    input,
    policy({
      clusterSimilarityThreshold: 0.5,
      mergeSimilarityThreshold: 0.82,
      rotationHysteresis: 0.06,
    }),
    NOW,
  );

  assert.deepEqual(runOne.clusters, runTwo.clusters);
});
