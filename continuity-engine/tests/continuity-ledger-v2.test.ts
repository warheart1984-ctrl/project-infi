import { test } from "node:test";
import assert from "node:assert/strict";
import { annotateCorrigibility } from "../src/judgment/cycle";
import { InMemoryContinuityLedger } from "../src/ledger/continuity-ledger";
import {
  applyGovernanceWithRealityVeto,
  detectRealityVeto,
  processRealityVeto,
} from "../src/governance/reality-veto";

const soundCycle = annotateCorrigibility({
  id: "jc-1",
  observerId: "steward-1",
  timestamp: "2026-06-19T00:00:00.000Z",
  observation: { signal: "latency_p99", value: 120 },
  interpretation: { alternatives: [{ label: "load", description: "traffic spike" }] },
  valuation: { whatMatters: "user_experience" },
  decision: { actorId: "steward-1", action: "recalibrate" },
  context: { thresholdId: "T1" },
  outcome: { metrics: { latency: 120 } },
  feedback: { confirmed: true },
  reflection: { changes: ["raised_threshold"] },
  relatedThresholdIds: ["T1"],
});

const failedCycle = annotateCorrigibility({
  id: "jc-bad",
  observerId: "steward-2",
  timestamp: "2026-06-19T00:00:00.000Z",
  observation: null,
  interpretation: {},
  valuation: null,
  decision: {},
  context: {},
  outcome: {},
  feedback: {},
  reflection: {},
});

test("ContinuityLedger stores cycles and computes corrigibility", async () => {
  const ledger = new InMemoryContinuityLedger();
  await ledger.appendCycle(soundCycle);

  const stored = await ledger.getCycle("jc-1");
  assert.equal(stored?.corrigibilityStatus, "sound");
  assert.equal((await ledger.getLineageCorrigibility("steward-1")), "sound");
});

test("ContinuityLedger appends Reality Veto and threshold views", async () => {
  const ledger = new InMemoryContinuityLedger();
  await ledger.appendCycle(soundCycle);
  await ledger.appendRealityVeto({
    id: "rv-1",
    timestamp: "2026-06-19T01:00:00.000Z",
    observerId: "steward-1",
    violatedExpectation: { thresholdId: "T1", predictedOutcome: 100 },
    observedOutcome: 200,
    evidence: { metric: "latency_p99" },
    severity: "major",
  });

  const vetoes = await ledger.getRealityVetoes();
  assert.equal(vetoes.length, 1);

  const views = await ledger.getThresholdViews();
  assert.equal(views.length, 1);
  assert.equal(views[0]!.thresholdId, "T1");
  assert.equal(views[0]!.relatedVetoCount, 1);
});

test("getFailedLineages detects collapsed corrigibility", async () => {
  const ledger = new InMemoryContinuityLedger();
  await ledger.appendCycle(failedCycle);

  const failed = await ledger.getFailedLineages();
  assert.deepEqual(failed, ["steward-2"]);
});

test("getContinuityHealth reports at-risk when F-1 present locally", async () => {
  const ledger = new InMemoryContinuityLedger();
  await ledger.appendCycle(soundCycle);
  await ledger.appendCycle(failedCycle);

  const health = await ledger.getContinuityHealth();
  assert.equal(health.health, "at-risk");
  assert.ok(health.failureModes.includes("F-1"));
  assert.equal(health.soundLineageCount, 1);
  assert.equal(health.failedLineageCount, 1);
});

test("getContinuityHealth reports collapsed when F-3 holds", async () => {
  const ledger = new InMemoryContinuityLedger();
  await ledger.appendCycle(failedCycle);
  await ledger.appendRealityVeto({
    id: "rv-suppressed",
    timestamp: "2026-06-19T03:00:00.000Z",
    violatedExpectation: 100,
    observedOutcome: 300,
    evidence: { blocked: true },
    severity: "critical",
    suppressed: true,
  });

  const health = await ledger.getContinuityHealth();
  assert.equal(health.health, "collapsed");
  assert.ok(health.failureModes.includes("F-3"));
});

test("detectRealityVeto returns receipt when tolerance fails", () => {
  const veto = detectRealityVeto(
    { id: "exp-1", description: "latency bound", predictedOutcome: 100 },
    { id: "obs-1", outcome: 200, evidence: { p99: 200 } },
    (pred, actual) => pred === actual,
    { observerId: "steward-1" },
  );

  assert.ok(veto);
  assert.equal(veto!.severity, "major");
  assert.equal(veto!.id, "rv_obs-1");
});

test("processRealityVeto appends veto and mandatory reconsideration cycle", async () => {
  const ledger = new InMemoryContinuityLedger();
  const veto = {
    id: "rv-2",
    timestamp: "2026-06-19T02:00:00.000Z",
    violatedExpectation: 100,
    observedOutcome: 250,
    evidence: { mismatch: true },
    severity: "major" as const,
  };

  const cycle = await processRealityVeto(ledger, veto);
  assert.equal(cycle.tags?.includes("reality-veto"), true);
  assert.equal((await ledger.getRealityVetoes()).length, 1);
  assert.ok(await ledger.getCycle(cycle.id));
});

test("applyGovernanceWithRealityVeto blocks failed corrigibility", () => {
  const result = applyGovernanceWithRealityVeto(failedCycle, {
    allowed: true,
    reasons: ["base ok"],
  });

  assert.equal(result.allowed, false);
  assert.ok(result.reasons.some((r) => r.includes("non-corrigible")));
});

test("applyGovernanceWithRealityVeto passes sound cycles", () => {
  const result = applyGovernanceWithRealityVeto(soundCycle, {
    allowed: true,
    reasons: ["base ok"],
  });

  assert.equal(result.allowed, true);
});
