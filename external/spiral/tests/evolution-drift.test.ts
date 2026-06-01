import assert from "node:assert/strict";
import test from "node:test";
import {
  buildDriftSamplesFromLedger,
  computeInvariantPressureIndex,
  deriveDriftTrajectoryFromLedger,
  evaluateAutonomyDriftBudget,
  evaluateExploratoryMicroDelta,
  type EvolutionLedgerLikeEntry,
} from "../server/evolution-drift";

function entry(input: Partial<EvolutionLedgerLikeEntry>): EvolutionLedgerLikeEntry {
  return {
    timestamp: input.timestamp || 1,
    principalId: input.principalId || "anon:test",
    type: input.type || "cycle-applied",
    ...(input.cycleId ? { cycleId: input.cycleId } : {}),
    ...(input.mode ? { mode: input.mode } : {}),
    ...(input.driftIndex ? { driftIndex: input.driftIndex } : {}),
  };
}

test("deriveDriftTrajectoryFromLedger handles empty windows", () => {
  const metrics = deriveDriftTrajectoryFromLedger([], {
    now: 100,
  });
  assert.equal(metrics.sampleCount, 0);
  assert.equal(metrics.latestCycleId, null);
  assert.equal(metrics.latest.driftVelocity, 0);
  assert.equal(metrics.latest.stabilityIndex, 1);
});

test("deriveDriftTrajectoryFromLedger handles fewer than five cycles", () => {
  const entries: EvolutionLedgerLikeEntry[] = [
    entry({
      timestamp: 1,
      cycleId: 1,
      mode: "wild",
      driftIndex: {
        filesTouched: 2,
        linesAdded: 10,
        linesDeleted: 2,
        semanticDiffScore: 0.2,
        invariantImpact: "low",
      },
    }),
    entry({
      timestamp: 2,
      cycleId: 2,
      mode: "wild",
      driftIndex: {
        filesTouched: 2,
        linesAdded: 12,
        linesDeleted: 3,
        semanticDiffScore: 0.25,
        invariantImpact: "medium",
      },
    }),
    entry({
      timestamp: 3,
      cycleId: 3,
      mode: "wild",
      driftIndex: {
        filesTouched: 3,
        linesAdded: 9,
        linesDeleted: 4,
        semanticDiffScore: 0.22,
        invariantImpact: "none",
      },
    }),
  ];
  const metrics = deriveDriftTrajectoryFromLedger(entries, { now: 300 });
  assert.equal(metrics.sampleCount, 3);
  assert.equal(metrics.windows["5c"].count, 3);
  assert.ok(Number.isFinite(metrics.windows["5c"].driftVelocity));
  assert.ok(Number.isFinite(metrics.windows["5c"].stabilityIndex));
});

test("buildDriftSamplesFromLedger supports mixed STILL/WILD filtering", () => {
  const entries: EvolutionLedgerLikeEntry[] = [
    entry({
      timestamp: 1,
      cycleId: 1,
      mode: "still",
      driftIndex: {
        filesTouched: 1,
        linesAdded: 1,
        linesDeleted: 0,
        semanticDiffScore: 0.1,
        invariantImpact: "none",
      },
    }),
    entry({
      timestamp: 2,
      cycleId: 2,
      mode: "wild",
      driftIndex: {
        filesTouched: 2,
        linesAdded: 4,
        linesDeleted: 2,
        semanticDiffScore: 0.3,
        invariantImpact: "low",
      },
    }),
  ];
  const allSamples = buildDriftSamplesFromLedger(entries, { modeFilter: "all" });
  const wildSamples = buildDriftSamplesFromLedger(entries, { modeFilter: "wild" });
  const stillSamples = buildDriftSamplesFromLedger(entries, { modeFilter: "still" });
  assert.equal(allSamples.length, 2);
  assert.equal(wildSamples.length, 1);
  assert.equal(stillSamples.length, 1);
  assert.equal(wildSamples[0].mode, "wild");
  assert.equal(stillSamples[0].mode, "still");
});

test("deriveDriftTrajectoryFromLedger handles zero semanticDiffScore cycles", () => {
  const entries: EvolutionLedgerLikeEntry[] = Array.from({ length: 6 }, (_, index) =>
    entry({
      timestamp: index + 1,
      cycleId: index + 1,
      mode: "wild",
      driftIndex: {
        filesTouched: 2,
        linesAdded: 0,
        linesDeleted: 0,
        semanticDiffScore: 0,
        invariantImpact: "none",
      },
    }),
  );
  const metrics = deriveDriftTrajectoryFromLedger(entries, { now: 500 });
  assert.equal(metrics.windows["5c"].driftVelocity, 0);
  assert.equal(metrics.windows["5c"].stabilityIndex, 1);
  assert.ok(Number.isFinite(metrics.windows["5c"].refactorDensity));
});

test("deriveDriftTrajectoryFromLedger is deterministic for repeated identical cycles", () => {
  const entries: EvolutionLedgerLikeEntry[] = Array.from({ length: 8 }, (_, index) =>
    entry({
      timestamp: index + 1,
      cycleId: index + 1,
      mode: "wild",
      driftIndex: {
        filesTouched: 2,
        linesAdded: 12,
        linesDeleted: 8,
        semanticDiffScore: 0.3,
        invariantImpact: "medium",
      },
    }),
  );
  const first = deriveDriftTrajectoryFromLedger(entries, { now: 800 });
  const second = deriveDriftTrajectoryFromLedger(entries, { now: 800 });
  assert.deepEqual(first, second);
  assert.equal(first.windows["5c"].driftVelocity, 0);
});

test("computeInvariantPressureIndex computes weighted frequency deterministically", () => {
  const entries: EvolutionLedgerLikeEntry[] = [
    entry({
      timestamp: 1,
      cycleId: 1,
      mode: "wild",
      driftIndex: {
        filesTouched: 1,
        linesAdded: 1,
        linesDeleted: 0,
        semanticDiffScore: 0.1,
        invariantImpact: "low",
      },
    }),
    entry({
      timestamp: 2,
      cycleId: 2,
      mode: "wild",
      driftIndex: {
        filesTouched: 1,
        linesAdded: 2,
        linesDeleted: 0,
        semanticDiffScore: 0.2,
        invariantImpact: "high",
      },
    }),
    entry({
      timestamp: 3,
      cycleId: 3,
      mode: "wild",
      driftIndex: {
        filesTouched: 1,
        linesAdded: 0,
        linesDeleted: 0,
        semanticDiffScore: 0.05,
        invariantImpact: "none",
      },
    }),
  ];
  const samples = buildDriftSamplesFromLedger(entries, { modeFilter: "wild" });
  const index = computeInvariantPressureIndex({
    samples,
    windowSize: 3,
    impactWeights: {
      none: 0,
      low: 0.25,
      medium: 0.5,
      high: 1,
    },
  });
  assert.equal(index.count, 3);
  assert.equal(index.impactFrequency.none, 1);
  assert.equal(index.impactFrequency.low, 1);
  assert.equal(index.impactFrequency.high, 1);
  assert.equal(index.value, 0.416667);
});

test("evaluateAutonomyDriftBudget blocks when candidate touches too many files", () => {
  const result = evaluateAutonomyDriftBudget({
    samples: [],
    candidate: {
      filesTouched: 7,
      linesAdded: 12,
      linesDeleted: 4,
      semanticDiffScore: 0.4,
      invariantImpact: "medium",
    },
    budget: {
      maxCumulativeDelta: 3,
      windowSize: 10,
      maxFilesTouched: 5,
    },
  });
  assert.equal(result.allowed, false);
  assert.equal(result.reasonCode, "AUTONOMY_DRIFT_BUDGET_MAX_FILES_EXCEEDED");
});

test("evaluateAutonomyDriftBudget blocks when projected cumulative delta exceeds budget", () => {
  const historyEntries: EvolutionLedgerLikeEntry[] = [
    entry({
      timestamp: 1,
      cycleId: 1,
      mode: "wild",
      driftIndex: {
        filesTouched: 1,
        linesAdded: 0,
        linesDeleted: 0,
        semanticDiffScore: 1,
        invariantImpact: "high",
      },
    }),
  ];
  const historySamples = buildDriftSamplesFromLedger(historyEntries, {
    modeFilter: "wild",
  });
  const result = evaluateAutonomyDriftBudget({
    samples: historySamples,
    candidate: {
      filesTouched: 1,
      linesAdded: 0,
      linesDeleted: 0,
      semanticDiffScore: 1,
      invariantImpact: "high",
    },
    budget: {
      maxCumulativeDelta: 1.5,
      windowSize: 2,
      maxFilesTouched: 4,
    },
  });
  assert.equal(result.allowed, false);
  assert.equal(result.reasonCode, "AUTONOMY_DRIFT_BUDGET_CUMULATIVE_EXCEEDED");
  assert.equal(result.projectedCumulativeDelta, 2);
});

test("evaluateExploratoryMicroDelta blocks candidate over exploratory micro-delta limits", () => {
  const result = evaluateExploratoryMicroDelta({
    candidate: {
      filesTouched: 3,
      linesAdded: 90,
      linesDeleted: 10,
      semanticDiffScore: 0.2,
      invariantImpact: "low",
    },
    budget: {
      maxFilesTouched: 2,
      maxLinesAdded: 100,
      maxLinesDeleted: 100,
      maxSemanticDiffScore: 0.3,
    },
  });
  assert.equal(result.allowed, false);
  assert.equal(result.reasonCode, "AUTONOMY_EXPLORATORY_MICRO_DELTA_MAX_FILES_EXCEEDED");
});

test("evaluateExploratoryMicroDelta allows candidate inside exploratory micro-delta limits", () => {
  const result = evaluateExploratoryMicroDelta({
    candidate: {
      filesTouched: 1,
      linesAdded: 24,
      linesDeleted: 12,
      semanticDiffScore: 0.15,
      invariantImpact: "none",
    },
    budget: {
      maxFilesTouched: 2,
      maxLinesAdded: 50,
      maxLinesDeleted: 30,
      maxSemanticDiffScore: 0.2,
    },
  });
  assert.equal(result.allowed, true);
  assert.equal(result.reasonCode, "OK");
});
