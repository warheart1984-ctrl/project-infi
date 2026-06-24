import { test } from "node:test";
import assert from "node:assert/strict";
import { enforceCRKOnThresholdDelta } from "../src/crk1/recalibration-guard";
import { defaultInvariantSet } from "../src/crk1/invariants";
import {
  RecalibrationGovernanceEngine,
  buildRecalibrationProposal,
} from "../src/governance/governance-engine";
import { applyDeltaWithCRKGuard } from "../src/governance/governed-apply";
import { InMemoryThresholdRegistry } from "../src/registry/memory-threshold-registry";
import type { InvariantSet, Threshold } from "../src/css2/types";

const baseThreshold = (): Threshold => ({
  id: "T1",
  name: "latency",
  domain: "Ops",
  metric: "p99_ms",
  comparator: ">",
  value: 100,
  intent: "Keep latency bounded",
  version: 1,
  active: true,
  createdAt: "2026-01-01T00:00:00.000Z",
  createdBy: "system",
  lastUpdatedAt: "2026-01-01T00:00:00.000Z",
  lastUpdatedBy: "system",
});

const soundJudgment = {
  vector: {
    perception: 0.7,
    interpretation: 0.7,
    valuation: 0.7,
    deliberation: 0.7,
    commitment: 0.7,
    reflection: 0.7,
  },
  compositeScore: 0.7,
  weakest: "reflection" as const,
  observationSufficient: true,
  judgmentSound: true,
  notes: [],
};

test("CRK-1 blocks non-derogable invariant violations", () => {
  const invSet: InvariantSet = {
    invariants: [
      {
        id: "INV_TEST",
        description: "value cannot increase",
        nonDerogable: true,
        checkThresholdChange: (before, after) =>
          typeof before.value === "number" &&
          typeof after.value === "number" &&
          after.value > before.value,
      },
    ],
  };

  const before = {
    id: "T1",
    name: "t",
    domain: "d",
    metric: "m",
    comparator: ">",
    value: 3,
    intent: "test",
    version: 1,
    active: true,
    createdAt: "",
    createdBy: "a",
    lastUpdatedAt: "",
    lastUpdatedBy: "a",
  };

  const result = enforceCRKOnThresholdDelta(
    { thresholdId: "T1", before, after: { value: 5 }, rationale: "" },
    invSet,
  );

  assert.equal(result.allowed, false);
});

test("governance engine rejects Δ-threshold without evidence (CRK-1.J)", async () => {
  const engine = new RecalibrationGovernanceEngine();
  const th = baseThreshold();
  const delta = buildRecalibrationProposal(th, 120, "Increase bound");

  const event = await engine.evaluate({
    delta,
    invSet: defaultInvariantSet,
    evidence: [],
  });

  assert.notEqual(event.decision, "approved");
  assert.ok(event.legitimateJudgment);
  assert.equal(event.legitimateJudgment!.legitimate, false);
  assert.ok(event.legitimacyBasis.includes("CRK-1.J"));
});

test("governance engine approves Δ-threshold with evidence and sound judgment", async () => {
  const engine = new RecalibrationGovernanceEngine();
  const th = baseThreshold();
  const delta = buildRecalibrationProposal(th, 120, "Evidence-backed recalibration");

  const event = await engine.evaluate({
    delta,
    invSet: defaultInvariantSet,
    evidence: [{ id: "ev-1", type: "observation" }],
    judgmentAssessment: soundJudgment,
  });

  assert.equal(event.decision, "approved");
  assert.equal(event.legitimateJudgment!.legitimate, true);
});

test("governance engine rejects core identity intent change (CRK-1.J stewardship)", async () => {
  const engine = new RecalibrationGovernanceEngine();
  const th = {
    ...baseThreshold(),
    domain: "Core",
    intent: "mission continuity anchor",
  };
  const delta = {
    thresholdId: th.id,
    before: th,
    after: { value: 120, intent: "different mission" },
    rationale: "Intent shift",
  };

  const event = await engine.evaluate({
    delta,
    invSet: defaultInvariantSet,
    evidence: [{ id: "ev-1" }],
    judgmentAssessment: soundJudgment,
  });

  assert.equal(event.decision, "rejected");
  assert.ok(event.legitimateJudgment!.gaps.some((g) => g.includes("Stewardship")));
});

test("applyDeltaWithCRKGuard blocks apply when CRK-1.J fails", async () => {
  const registry = new InMemoryThresholdRegistry();
  const th = await registry.create({
    name: "latency",
    domain: "Ops",
    metric: "p99_ms",
    comparator: ">",
    value: 100,
    intent: "bound",
    createdBy: "test",
  });

  const delta = buildRecalibrationProposal(th, 110, "no evidence");
  const result = await applyDeltaWithCRKGuard(
    registry,
    delta,
    "steward-1",
    defaultInvariantSet,
  );

  assert.equal(result.applied, false);
  assert.equal(result.legitimate, false);
  assert.ok(result.reason?.includes("CRK-1.J"));
});

test("governance engine rejects Δ-threshold when corrigibility fails", async () => {
  const engine = new RecalibrationGovernanceEngine();
  const th = baseThreshold();
  const delta = buildRecalibrationProposal(th, 120, "Evidence-backed recalibration");

  const event = await engine.evaluate({
    delta,
    invSet: defaultInvariantSet,
    evidence: [{ id: "ev-1", type: "observation" }],
    judgmentAssessment: soundJudgment,
    judgmentCycle: {
      id: "jc-bad",
      observerId: "steward-1",
      timestamp: "2026-06-19T00:00:00.000Z",
      observation: null,
      interpretation: {},
      valuation: null,
      decision: {},
      context: {},
      outcome: {},
      feedback: {},
      reflection: {},
    },
  });

  assert.equal(event.decision, "rejected");
  assert.ok(event.legitimacyBasis.includes("CRK-1.J"));
  assert.ok(event.legitimateJudgment!.failedRequirements.includes("corrigibility"));
});

test("applyDeltaWithCRKGuard applies when CRK-1.J satisfied", async () => {
  const registry = new InMemoryThresholdRegistry();
  const th = await registry.create({
    name: "latency",
    domain: "Ops",
    metric: "p99_ms",
    comparator: ">",
    value: 100,
    intent: "bound",
    createdBy: "test",
  });

  const delta = buildRecalibrationProposal(th, 110, "evidence-backed");
  const result = await applyDeltaWithCRKGuard(
    registry,
    delta,
    "steward-1",
    defaultInvariantSet,
    {
      evidence: [{ id: "ev-1" }],
      judgmentAssessment: soundJudgment,
    },
  );

  assert.equal(result.applied, true);
  assert.equal(result.legitimate, true);
  assert.equal(result.threshold?.value, 110);
});

test("governance engine blocks Δ-threshold when Reality Veto ignored (RPA-1)", async () => {
  const engine = new RecalibrationGovernanceEngine();
  const th = baseThreshold();
  const delta = buildRecalibrationProposal(th, 120, "Attempt after ignored veto");

  const event = await engine.evaluate({
    delta,
    invSet: defaultInvariantSet,
    evidence: [{ id: "ev-1" }],
    judgmentAssessment: soundJudgment,
    realityVeto: {
      id: "rv-1",
      timestamp: "2026-06-24T00:00:00.000Z",
      observerId: "steward-1",
      violatedExpectation: 100,
      observedOutcome: 200,
      evidence: { mismatch: true },
      severity: "major",
    },
    realityVetoIgnored: true,
  });

  assert.equal(event.decision, "rejected");
  assert.ok(event.legitimacyBasis.includes("RPA-1"));
});
