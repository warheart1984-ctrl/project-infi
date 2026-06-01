import assert from "node:assert/strict";
import test from "node:test";
import type { Memory } from "../shared/schema";
import { applyRotationalMemoryPruning, type MemoryRotationPolicy } from "../server/memory-rotation";
import {
  computeRotationShadowTelemetry,
  summarizeRotationShadowTelemetry,
} from "../server/memory-rotation-shadow";

const DAY_MS = 24 * 60 * 60 * 1000;
const NOW = Date.UTC(2026, 1, 26);

function buildMemory(overrides: Partial<Memory> = {}): Memory {
  return {
    id: overrides.id ?? `m-${Math.random().toString(36).slice(2, 9)}`,
    content: overrides.content ?? "default memory content",
    principalId: overrides.principalId ?? "test:principal",
    memoryType: overrides.memoryType ?? "observation",
    source: overrides.source ?? "live",
    confidenceScore: overrides.confidenceScore ?? 0.72,
    status: overrides.status ?? "active",
    domain: overrides.domain ?? "operational",
    createdAt: overrides.createdAt ?? NOW - 90 * DAY_MS,
    updatedAt: overrides.updatedAt ?? NOW - DAY_MS,
    lastUsedAt: overrides.lastUsedAt ?? NOW - DAY_MS,
    lastConfirmedAt: overrides.lastConfirmedAt ?? NOW - 45 * DAY_MS,
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
    clusterSimilarityThreshold: 0.55,
    mergeSimilarityThreshold: 0.9,
    rotationHysteresis: 0.08,
    activeSlotsPerCluster: 1,
    maxActivePerGroup: 64,
    recencyHalfLifeDays: 21,
    reactivationWindowDays: 10,
    driftPenaltyWeight: 0.45,
    mergeConfidenceGain: 0.35,
    mergeResurfaceGain: 0.45,
    ...overrides,
  };
}

test("shadow telemetry is deterministic for fixed inputs", async () => {
  const memories = [
    buildMemory({
      id: "a",
      content: "deployment pipeline checklist for release",
      source: "import-summary",
    }),
    buildMemory({
      id: "b",
      content: "release deployment checklist for pipeline",
      source: "import-summary",
      status: "quiet",
    }),
    buildMemory({
      id: "c",
      content: "observability dashboard alert routing",
      source: "manual-demoted-anchor",
    }),
  ];
  const result = applyRotationalMemoryPruning(memories, policy(), NOW);

  const first = await computeRotationShadowTelemetry({
    memories,
    result,
    includeSample: true,
    sampleSize: 10,
    now: NOW,
    persistCache: false,
  });
  const second = await computeRotationShadowTelemetry({
    memories,
    result,
    includeSample: true,
    sampleSize: 10,
    now: NOW,
    persistCache: false,
  });

  assert.deepEqual(first.telemetry, second.telemetry);
  assert.deepEqual(first.sample, second.sample);
});

test("shadow telemetry classifies lexical stronger than semantic disagreements", async () => {
  const memories = [
    buildMemory({
      id: "lex-a",
      content: "deployment checklist release pipeline",
      source: "import-summary",
    }),
    buildMemory({
      id: "lex-b",
      content: "release pipeline deployment checklist",
      source: "import-summary",
    }),
  ];
  const result = applyRotationalMemoryPruning(
    memories,
    policy({ clusterSimilarityThreshold: 0.45, mergeSimilarityThreshold: 2 }),
    NOW,
  );
  const shadow = await computeRotationShadowTelemetry({
    memories,
    result,
    includeSample: true,
    sampleSize: 10,
    now: NOW,
    persistCache: false,
    embedder: (memory) => (memory.id === "lex-a" ? [1, 0, 0] : [0, 1, 0]),
  });

  assert.ok(shadow.telemetry.disagreement_buckets.LEXICAL_STRONGER_THAN_SEMANTIC >= 1);
  assert.ok(shadow.sample.some((pair) => pair.bucket === "LEXICAL_STRONGER_THAN_SEMANTIC"));
});

test("shadow telemetry summary computes windows and ewma", () => {
  const records = [
    {
      timestamp: NOW - 2 * DAY_MS,
      shadow: {
        embeddingModel: "local-hash-embed.v1.0.0",
        semantic_stats: {
          lexical_mean: 0.4,
          lexical_var: 0.03,
          semantic_mean: 0.42,
          semantic_var: 0.02,
          mean_disagreement: 0.12,
          disagreement_rate: 0.3,
          semantic_top1_share: 0.4,
        },
        disagreement_buckets: {
          SEMANTIC_STRONGER_THAN_LEXICAL: 2,
          LEXICAL_STRONGER_THAN_SEMANTIC: 3,
          BOTH_STRONG: 1,
          BOTH_WEAK: 0,
          NEAR_MATCH: 4,
        },
        clusters: [],
      },
    },
    {
      timestamp: NOW - DAY_MS,
      shadow: {
        embeddingModel: "local-hash-embed.v1.0.0",
        semantic_stats: {
          lexical_mean: 0.45,
          lexical_var: 0.02,
          semantic_mean: 0.5,
          semantic_var: 0.03,
          mean_disagreement: 0.1,
          disagreement_rate: 0.2,
          semantic_top1_share: 0.35,
        },
        disagreement_buckets: {
          SEMANTIC_STRONGER_THAN_LEXICAL: 1,
          LEXICAL_STRONGER_THAN_SEMANTIC: 1,
          BOTH_STRONG: 2,
          BOTH_WEAK: 1,
          NEAR_MATCH: 5,
        },
        clusters: [],
      },
    },
  ];

  const summary = summarizeRotationShadowTelemetry(records, NOW);
  assert.equal(summary.totalRuns, 2);
  assert.equal(summary.embeddingModel, "local-hash-embed.v1.0.0");
  assert.equal(summary.runWindows["10r"].count, 2);
  assert.ok(summary.ewma.mean_disagreement > 0);
  assert.ok(summary.disagreement_buckets.NEAR_MATCH >= 1);
});
