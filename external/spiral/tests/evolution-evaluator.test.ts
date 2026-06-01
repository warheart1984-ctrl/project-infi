import assert from "node:assert/strict";
import test from "node:test";
import { evaluateExecutiveAutonomy } from "../server/evolution-evaluator";
import type { EvolutionLedgerLikeEntry } from "../server/evolution-drift";

function entry(input: Partial<EvolutionLedgerLikeEntry>): EvolutionLedgerLikeEntry {
  return {
    timestamp: input.timestamp || 1,
    principalId: input.principalId || "anon:autonomy-test",
    type: input.type || "cycle-applied",
    ...(input.cycleId ? { cycleId: input.cycleId } : {}),
    ...(input.mode ? { mode: input.mode } : {}),
    ...(input.driftIndex ? { driftIndex: input.driftIndex } : {}),
  };
}

test("evaluateExecutiveAutonomy emits deterministic shadow proposal metadata", async () => {
  const evaluation = await evaluateExecutiveAutonomy({
    principalId: "anon:autonomy-test-shadow",
    now: 10_000,
    thresholds: {
      driftVelocityAbsThreshold: 0,
      stabilityIndexFloor: 1,
      invariantPressureCeiling: 0,
      structuralEntropyCeiling: 0,
    },
    runnerConfig: {
      evaluationIntervalMs: 1,
      triggerCooldownMs: 1,
      entropyWindowSize: 5,
      exploratoryEnabled: true,
      exploratoryPulseCadence: 6,
      exploratoryMinimumSampleCount: 6,
    },
  });

  assert.equal(evaluation.triggered, true);
  assert.equal(evaluation.shadow.authority, "shadow");
  assert.ok((evaluation.signal || "").startsWith("autonomy:"));
});

test("evaluateExecutiveAutonomy enforces trigger cooldown deterministically", async () => {
  const principalId = "anon:autonomy-test-cooldown";
  const first = await evaluateExecutiveAutonomy({
    principalId,
    now: 20_000,
    thresholds: {
      driftVelocityAbsThreshold: 0,
      stabilityIndexFloor: 1,
      invariantPressureCeiling: 0,
      structuralEntropyCeiling: 0,
    },
    runnerConfig: {
      evaluationIntervalMs: 1,
      triggerCooldownMs: 60_000,
      entropyWindowSize: 5,
      exploratoryEnabled: true,
      exploratoryPulseCadence: 6,
      exploratoryMinimumSampleCount: 6,
    },
  });
  assert.equal(first.triggered, true);

  const second = await evaluateExecutiveAutonomy({
    principalId,
    now: 20_100,
    thresholds: {
      driftVelocityAbsThreshold: 0,
      stabilityIndexFloor: 1,
      invariantPressureCeiling: 0,
      structuralEntropyCeiling: 0,
    },
    runnerConfig: {
      evaluationIntervalMs: 1,
      triggerCooldownMs: 60_000,
      entropyWindowSize: 5,
      exploratoryEnabled: true,
      exploratoryPulseCadence: 6,
      exploratoryMinimumSampleCount: 6,
    },
  });
  assert.equal(second.triggered, false);
  assert.ok(second.reasonCodes.includes("AUTONOMY_TRIGGER_COOLDOWN_ACTIVE"));
});

test("evaluateExecutiveAutonomy emits exploratory pulse once per sample-count cadence", async () => {
  const principalId = "anon:autonomy-test-exploratory";
  const ledgerEntries: EvolutionLedgerLikeEntry[] = [
    entry({
      principalId,
      timestamp: 1,
      cycleId: 1,
      mode: "wild",
      driftIndex: {
        filesTouched: 1,
        linesAdded: 4,
        linesDeleted: 0,
        semanticDiffScore: 0.1,
        invariantImpact: "low",
      },
    }),
    entry({
      principalId,
      timestamp: 2,
      cycleId: 2,
      mode: "wild",
      driftIndex: {
        filesTouched: 1,
        linesAdded: 4,
        linesDeleted: 0,
        semanticDiffScore: 0.1,
        invariantImpact: "low",
      },
    }),
    entry({
      principalId,
      timestamp: 3,
      cycleId: 3,
      mode: "wild",
      driftIndex: {
        filesTouched: 1,
        linesAdded: 4,
        linesDeleted: 0,
        semanticDiffScore: 0.1,
        invariantImpact: "low",
      },
    }),
    entry({
      principalId,
      timestamp: 4,
      cycleId: 4,
      mode: "wild",
      driftIndex: {
        filesTouched: 1,
        linesAdded: 4,
        linesDeleted: 0,
        semanticDiffScore: 0.1,
        invariantImpact: "low",
      },
    }),
  ];

  const first = await evaluateExecutiveAutonomy({
    principalId,
    now: 50_000,
    ledgerEntries,
    thresholds: {
      driftVelocityAbsThreshold: 1,
      stabilityIndexFloor: 0,
      invariantPressureCeiling: 1,
      structuralEntropyCeiling: 1,
    },
    runnerConfig: {
      evaluationIntervalMs: 1,
      triggerCooldownMs: 1,
      entropyWindowSize: 5,
      exploratoryEnabled: true,
      exploratoryPulseCadence: 2,
      exploratoryMinimumSampleCount: 2,
    },
  });

  assert.equal(first.triggered, true);
  assert.ok(first.reasonCodes.includes("AUTONOMY_TRIGGER_EXPLORATORY_PULSE"));
  assert.equal(first.runner.exploratoryPulseDue, true);

  const second = await evaluateExecutiveAutonomy({
    principalId,
    now: 50_100,
    ledgerEntries,
    thresholds: {
      driftVelocityAbsThreshold: 1,
      stabilityIndexFloor: 0,
      invariantPressureCeiling: 1,
      structuralEntropyCeiling: 1,
    },
    runnerConfig: {
      evaluationIntervalMs: 1,
      triggerCooldownMs: 1,
      entropyWindowSize: 5,
      exploratoryEnabled: true,
      exploratoryPulseCadence: 2,
      exploratoryMinimumSampleCount: 2,
    },
  });

  assert.equal(second.triggered, false);
  assert.ok(second.reasonCodes.includes("AUTONOMY_TRIGGER_NONE"));
  assert.equal(second.runner.exploratoryPulseDue, false);
});
