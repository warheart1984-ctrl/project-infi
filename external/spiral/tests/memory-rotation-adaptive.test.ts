import assert from "node:assert/strict";
import test from "node:test";
import { mkdtemp, readFile } from "fs/promises";
import os from "os";
import path from "path";
import type { Memory } from "../shared/schema";
import type { MemoryRotationResult } from "../server/memory-rotation";
import {
  appendRotationTelemetryRecord,
  buildAdaptiveRecommendation,
  buildRotationTelemetryRecord,
  createDefaultAdaptiveState,
  ROTATION_METRICS_SCHEMA_VERSION,
  simulateAdaptiveReplay,
  summarizeRotationTelemetry,
  type MemoryRotationTelemetryRecordV2,
} from "../server/memory-rotation-adaptive";
import { getMemoryRotationPolicy } from "../server/memory-rotation";

const DAY_MS = 24 * 60 * 60 * 1000;
const NOW = Date.UTC(2026, 1, 25);

function buildMemory(overrides: Partial<Memory> = {}): Memory {
  return {
    id: overrides.id ?? `m-${Math.random().toString(36).slice(2, 9)}`,
    content: overrides.content ?? "alpha beta memory strand",
    principalId: overrides.principalId ?? "test:principal",
    memoryType: overrides.memoryType ?? "observation",
    source: overrides.source ?? "live",
    confidenceScore: overrides.confidenceScore ?? 0.7,
    status: overrides.status ?? "active",
    domain: overrides.domain ?? "operational",
    createdAt: overrides.createdAt ?? NOW - 90 * DAY_MS,
    updatedAt: overrides.updatedAt ?? NOW - DAY_MS,
    lastUsedAt: overrides.lastUsedAt ?? NOW - DAY_MS,
    lastConfirmedAt: overrides.lastConfirmedAt ?? NOW - 90 * DAY_MS,
    halfLifeDays: overrides.halfLifeDays ?? 45,
    requiresConfirmation: overrides.requiresConfirmation ?? false,
    intentBias: overrides.intentBias ?? -0.3,
    confirmationPrompted: overrides.confirmationPrompted ?? false,
    resurfaceCount: overrides.resurfaceCount ?? 0,
  };
}

function buildResult(memories: Memory[]): MemoryRotationResult {
  return {
    memories,
    changed: true,
    stats: {
      totalBefore: memories.length,
      totalAfter: memories.length,
      clusterCount: 2,
      changedClusterCount: 1,
      mergedCount: 1,
      deletedCount: 1,
      rotatedCount: 1,
      promotedCount: 1,
      demotedCount: 1,
      capacityDemotedCount: 0,
      quietGuardBlockedCount: 0,
    },
    clusters: [
      {
        clusterId: "c-alpha",
        groupKey: "test:principal::operational",
        changed: true,
        before: {
          representativeId: memories[0].id,
          memberIds: [memories[0].id, memories[1].id],
          activeIds: [memories[0].id],
          quietIds: [memories[1].id],
          size: 2,
        },
        after: {
          representativeId: memories[0].id,
          memberIds: [memories[0].id],
          activeIds: [memories[0].id],
          quietIds: [],
          size: 1,
        },
        actions: [],
        signals: {
          similarity: 0.9,
          hysteresis: null,
          cap: 96,
          topFeatures: ["alpha", "beta", "memory"],
        },
        scores: {
          [memories[0].id]: 0.91,
          [memories[1].id]: 0.74,
        },
      },
      {
        clusterId: "c-gamma",
        groupKey: "test:principal::operational",
        changed: false,
        before: {
          representativeId: memories[2].id,
          memberIds: [memories[2].id],
          activeIds: [memories[2].id],
          quietIds: [],
          size: 1,
        },
        after: {
          representativeId: memories[2].id,
          memberIds: [memories[2].id],
          activeIds: [memories[2].id],
          quietIds: [],
          size: 1,
        },
        actions: [],
        signals: {
          similarity: 0,
          hysteresis: null,
          cap: 96,
          topFeatures: ["delta", "epsilon"],
        },
        scores: {
          [memories[2].id]: 0.82,
        },
      },
    ],
  };
}

function syntheticRecord(index: number, overrides: Partial<MemoryRotationTelemetryRecordV2> = {}): MemoryRotationTelemetryRecordV2 {
  const timestamp = NOW - (20 - index) * DAY_MS;
  const baseVar = 0.1 + index * 0.002;
  const base = {
    schemaVersion: ROTATION_METRICS_SCHEMA_VERSION,
    runId: `run-${index}`,
    timestamp,
    durationMs: 10,
    applied: true as const,
    totals: { before: 30, after: 29, delta: -1 },
    stats: {
      clusterCount: 6,
      changedClusterCount: 2,
      mergedCount: 1,
      deletedCount: 1,
      rotatedCount: 1,
      promotedCount: 1,
      demotedCount: 1,
      capacityDemotedCount: 0,
      quietGuardBlockedCount: 0,
    },
    rates: {
      capDemotionRate: 0.01,
      changeRate: 0.18,
      demotionRate: 0.02,
      mergeRate: 0.03,
      quietGuardBlockRate: 0,
      representativeChurnRate: 0.09,
      rotationRate: 0.08,
    },
    field: {
      H_mean: 0.42,
      H_var: baseVar,
      H_skew: 0.1,
      H_repMemberDelta_mean: 0.02,
      H_top1_share: 0.31,
      H_hhi: 0.2,
      H_var_grad: 0.01,
      H_var_ac1: 0.4,
    },
    clusters: [
      { clusterId: "c1", H_cluster: 0.4, H_rep: 0.45, H_memberMean: 0.38 },
      { clusterId: "c2", H_cluster: 0.5, H_rep: 0.49, H_memberMean: 0.48 },
    ],
    thresholds: {
      activeSlotsPerCluster: 1,
      clusterSimilarityThreshold: 0.63,
      maxActivePerGroup: 96,
      mergeSimilarityThreshold: 0.86,
      reactivationWindowDays: 10,
      recencyHalfLifeDays: 21,
      rotationHysteresis: 0.08,
    },
  };
  return {
    ...base,
    ...overrides,
    rates: {
      ...base.rates,
      ...(overrides.rates || {}),
    },
    field: {
      ...base.field,
      ...(overrides.field || {}),
    },
    stats: {
      ...base.stats,
      ...(overrides.stats || {}),
    },
    thresholds: {
      ...base.thresholds,
      ...(overrides.thresholds || {}),
    },
  };
}

test("telemetry record includes entropy topology metrics and schema v2", () => {
  const memories = [
    buildMemory({ id: "m1", content: "alpha alpha beta beta gamma" }),
    buildMemory({ id: "m2", content: "alpha delta epsilon zeta eta" }),
    buildMemory({ id: "m3", content: "theta iota kappa lambda mu nu" }),
  ];
  const result = buildResult(memories);
  const policy = getMemoryRotationPolicy();
  const first = buildRotationTelemetryRecord({
    beforeMemories: memories,
    durationMs: 42,
    history: [],
    policy,
    result,
    timestamp: NOW,
  });
  assert.equal(first.schemaVersion, ROTATION_METRICS_SCHEMA_VERSION);
  assert.equal(first.applied, true);
  assert.ok(first.field.H_var >= 0);
  assert.ok(first.field.H_top1_share >= 0 && first.field.H_top1_share <= 1);
  assert.ok(first.field.H_hhi >= 0 && first.field.H_hhi <= 1);

  const second = buildRotationTelemetryRecord({
    beforeMemories: memories,
    durationMs: 42,
    history: [first],
    policy,
    result,
    timestamp: NOW + DAY_MS,
  });
  assert.ok(Number.isFinite(second.field.H_var_grad));
});

test("append telemetry enforces monotonic timestamps with deterministic key order", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "spiral-metrics-"));
  const filePath = path.join(dir, "metrics.jsonl");
  const recordA = syntheticRecord(1, { timestamp: NOW });
  const recordB = syntheticRecord(2, { timestamp: NOW });

  const savedA = await appendRotationTelemetryRecord(recordA, {
    filePath,
    nowFn: () => NOW,
  });
  const savedB = await appendRotationTelemetryRecord(recordB, {
    filePath,
    nowFn: () => NOW,
  });
  assert.ok(savedB.timestamp > savedA.timestamp, "Second telemetry record should increment timestamp.");

  const text = await readFile(filePath, "utf8");
  const firstLine = text.split(/\r?\n/g).find(Boolean) || "";
  assert.ok(firstLine.indexOf("\"applied\"") < firstLine.indexOf("\"clusters\""));
});

test("summary exposes dual windows and field alerts", () => {
  const records = Array.from({ length: 14 }, (_, index) =>
    syntheticRecord(index, {
      field: {
        H_mean: 0.4,
        H_var: 0.12 + index * 0.01,
        H_skew: 0.2,
        H_repMemberDelta_mean: 0.04,
        H_top1_share: 0.45,
        H_hhi: 0.32,
        H_var_grad: 0.02,
        H_var_ac1: 0.65,
      },
    }),
  );
  const summary = summarizeRotationTelemetry(records, NOW);
  assert.equal(summary.totalRuns, 14);
  assert.equal(summary.runWindows["10r"].count, 10);
  assert.ok(summary.timeWindows["7d"].count > 0);
  assert.equal(summary.fieldAlerts.entropy_skew_dominant_cluster, true);
});

test("adaptive recommendation separates effect and field layers", () => {
  const records = Array.from({ length: 12 }, (_, index) =>
    syntheticRecord(index, {
      rates: {
        capDemotionRate: 0.01,
        changeRate: 0.24,
        demotionRate: 0.02,
        mergeRate: 0.07,
        quietGuardBlockRate: 0,
        representativeChurnRate: 0.24,
        rotationRate: 0.16,
      },
      field: {
        H_mean: 0.43,
        H_var: 0.19 + index * 0.01,
        H_skew: 0.22,
        H_repMemberDelta_mean: 0.03,
        H_top1_share: 0.46,
        H_hhi: 0.33,
        H_var_grad: 0.02,
        H_var_ac1: 0.73,
      },
    }),
  );
  const state = createDefaultAdaptiveState(NOW);
  state.effectSignals.identity_churn_high.consecutive = 2;
  state.effectSignals.merge_saturation.consecutive = 2;
  state.fieldSignals.entropy_field_expanding.consecutive = 2;
  state.fieldSignals.entropy_skew_dominant_cluster.consecutive = 2;
  const recommendation = buildAdaptiveRecommendation({
    basePolicy: getMemoryRotationPolicy(),
    records,
    state,
    now: NOW,
  });
  assert.ok(recommendation.effect.deltas.length > 0, "Expected effect-layer deltas.");
  assert.ok(recommendation.field.deltas.length > 0, "Expected field-layer deltas.");
  assert.ok(recommendation.net.deltas.length > 0, "Expected net resolved deltas.");
});

test("replay convergence remains bounded under step-change entropy scenario", () => {
  const records: MemoryRotationTelemetryRecordV2[] = [];
  for (let i = 0; i < 12; i++) {
    records.push(
      syntheticRecord(i, {
        field: {
          H_mean: 0.34,
          H_var: 0.05,
          H_skew: 0.1,
          H_repMemberDelta_mean: 0.01,
          H_top1_share: 0.25,
          H_hhi: 0.18,
          H_var_grad: 0,
          H_var_ac1: 0.2,
        },
      }),
    );
  }
  for (let i = 12; i < 30; i++) {
    records.push(
      syntheticRecord(i, {
        field: {
          H_mean: 0.52,
          H_var: 0.2 + (i - 12) * 0.01,
          H_skew: 0.3,
          H_repMemberDelta_mean: 0.04,
          H_top1_share: 0.48,
          H_hhi: 0.35,
          H_var_grad: 0.03,
          H_var_ac1: 0.8,
        },
      }),
    );
  }
  const replay = simulateAdaptiveReplay({
    basePolicy: getMemoryRotationPolicy(),
    records,
  });
  assert.equal(replay.bounded, true);
  assert.ok(replay.steps >= 20);
});

test("sustained skew cannot ratchet maxActivePerGroup beyond configured band", () => {
  const records: MemoryRotationTelemetryRecordV2[] = [];
  for (let i = 0; i < 1000; i++) {
    records.push(
      syntheticRecord(i, {
        field: {
          H_mean: 0.5,
          H_var: 0.18,
          H_skew: 0.31,
          H_repMemberDelta_mean: 0.04,
          H_top1_share: 0.5,
          H_hhi: 0.36,
          H_var_grad: 0.02,
          H_var_ac1: 0.8,
        },
      }),
    );
  }

  const replay = simulateAdaptiveReplay({
    basePolicy: getMemoryRotationPolicy(),
    records,
  });

  assert.ok(replay.maxActivePerGroupRange <= 16, "maxActivePerGroup should stay within bounded adaptation band.");
});

test("sustained churn cannot ratchet merge/hysteresis beyond configured bands", () => {
  const records: MemoryRotationTelemetryRecordV2[] = [];
  for (let i = 0; i < 1000; i++) {
    records.push(
      syntheticRecord(i, {
        rates: {
          capDemotionRate: 0.01,
          changeRate: 0.27,
          demotionRate: 0.02,
          mergeRate: 0.08,
          quietGuardBlockRate: 0,
          representativeChurnRate: 0.27,
          rotationRate: 0.18,
        },
        field: {
          H_mean: 0.49,
          H_var: 0.2,
          H_skew: 0.26,
          H_repMemberDelta_mean: 0.03,
          H_top1_share: 0.47,
          H_hhi: 0.34,
          H_var_grad: 0.02,
          H_var_ac1: 0.79,
        },
      }),
    );
  }

  const replay = simulateAdaptiveReplay({
    basePolicy: getMemoryRotationPolicy(),
    records,
  });

  assert.ok(replay.rotationHysteresisRange <= 0.2, "rotationHysteresis should stay within base-relative adaptation band.");
  assert.ok(replay.mergeSimilarityRange <= 0.16, "mergeSimilarityThreshold should stay within base-relative adaptation band.");
});
