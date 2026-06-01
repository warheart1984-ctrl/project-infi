import assert from "node:assert/strict";
import test from "node:test";
import type { Memory } from "../shared/schema";
import {
  evaluateMemories,
  getMemoryPolicy,
  selectRelevantMemories,
} from "../server/memory-scoring";

const DAY_MS = 24 * 60 * 60 * 1000;

function buildMemory(overrides: Partial<Memory> = {}): Memory {
  const now = Date.now();
  return {
    id: overrides.id ?? `m-${Math.random().toString(36).slice(2, 9)}`,
    content: overrides.content ?? "alpha beta memory",
    principalId: overrides.principalId ?? "test:principal",
    memoryType: overrides.memoryType ?? "observation",
    source: overrides.source ?? "live",
    confidenceScore: overrides.confidenceScore ?? 0.72,
    status: overrides.status ?? "active",
    domain: overrides.domain ?? "operational",
    createdAt: overrides.createdAt ?? now - 90 * DAY_MS,
    updatedAt: overrides.updatedAt ?? now - DAY_MS,
    lastUsedAt: overrides.lastUsedAt ?? now - DAY_MS,
    lastConfirmedAt: overrides.lastConfirmedAt ?? now - 90 * DAY_MS,
    halfLifeDays: overrides.halfLifeDays ?? 45,
    requiresConfirmation: overrides.requiresConfirmation ?? false,
    intentBias: overrides.intentBias ?? -0.2,
    confirmationPrompted: overrides.confirmationPrompted ?? false,
    resurfaceCount: overrides.resurfaceCount ?? 0,
  };
}

test("memory scoring increases decay pressure when context entropy rises", () => {
  const now = Date.now();
  const candidate = buildMemory({
    id: "entropy-candidate",
    content: "alpha beta stable thread",
    createdAt: now - 180 * DAY_MS,
    lastConfirmedAt: now - 180 * DAY_MS,
    halfLifeDays: 90,
  });
  const policy = getMemoryPolicy();

  const lowEntropy = evaluateMemories(
    [candidate],
    "trace: alpha alpha alpha alpha beta",
    policy,
  )[0];
  const highEntropy = evaluateMemories(
    [candidate],
    "trace: alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu",
    policy,
  )[0];

  assert.ok(
    highEntropy.entropyPressure > lowEntropy.entropyPressure,
    "Higher context entropy should increase decay pressure.",
  );
  assert.ok(
    highEntropy.decayMultiplier < lowEntropy.decayMultiplier,
    "Higher context entropy should produce stronger decay (lower multiplier).",
  );
  assert.ok(lowEntropy.normalizedScore >= 0 && lowEntropy.normalizedScore <= 1);
  assert.ok(highEntropy.normalizedScore >= 0 && highEntropy.normalizedScore <= 1);
});

test("recurrence boost is recency-sensitive and avoids fossilized reinforcement", () => {
  const now = Date.now();
  const staleRepeated = buildMemory({
    id: "stale-repeated",
    content: "alpha beta legacy thread",
    confidenceScore: 0.78,
    resurfaceCount: 16,
    lastUsedAt: now - 120 * DAY_MS,
    createdAt: now - 260 * DAY_MS,
    lastConfirmedAt: now - 260 * DAY_MS,
    halfLifeDays: 220,
  });
  const recentRepeated = buildMemory({
    id: "recent-repeated",
    content: "alpha beta current thread",
    confidenceScore: 0.72,
    resurfaceCount: 4,
    lastUsedAt: now - 2 * DAY_MS,
    createdAt: now - 260 * DAY_MS,
    lastConfirmedAt: now - 260 * DAY_MS,
    halfLifeDays: 220,
  });

  const results = evaluateMemories(
    [staleRepeated, recentRepeated],
    "trace: alpha beta planning edge",
    getMemoryPolicy(),
  );
  const stale = results.find((item) => item.memory.id === "stale-repeated");
  const recent = results.find((item) => item.memory.id === "recent-repeated");
  assert.ok(stale && recent, "Expected both memory evaluations.");

  assert.ok(
    recent.recurrenceBoost > stale.recurrenceBoost,
    "Recurrence reinforcement should favor recent recurrence, not stale repetition.",
  );
  assert.ok(
    recent.fossilPenalty > stale.fossilPenalty,
    "Fossilization penalty should suppress stale repeated memory.",
  );
  assert.ok(
    recent.score > stale.score,
    "Recent meaningful recurrence should outrank stale repetition.",
  );
});

test("selection applies thematic compression to avoid near-duplicate memory fragments", () => {
  const now = Date.now();
  const duplicateA = buildMemory({
    id: "dup-a",
    content: "release pipeline alpha beta",
    createdAt: now - 10 * DAY_MS,
    lastConfirmedAt: now - 10 * DAY_MS,
  });
  const duplicateB = buildMemory({
    id: "dup-b",
    content: "alpha beta release pipeline",
    createdAt: now - 8 * DAY_MS,
    lastConfirmedAt: now - 8 * DAY_MS,
  });
  const distinct = buildMemory({
    id: "distinct",
    content: "observability alerting alpha beta",
    createdAt: now - 7 * DAY_MS,
    lastConfirmedAt: now - 7 * DAY_MS,
  });

  const policy = {
    ...getMemoryPolicy(),
    minPromptScore: 0.01,
    thematicSimilarityThreshold: 0.8,
  };
  const selected = selectRelevantMemories(
    [duplicateA, duplicateB, distinct],
    "trace: alpha beta release pipeline and observability alerting",
    3,
    policy,
  );
  const selectedIds = new Set(selected.map((memory) => memory.id));

  assert.ok(selectedIds.has("distinct"), "Distinct thematic memory should be retained.");
  const duplicateCount = Number(selectedIds.has("dup-a")) + Number(selectedIds.has("dup-b"));
  assert.equal(duplicateCount, 1, "Near-duplicate themes should be compressed to one memory.");
});
