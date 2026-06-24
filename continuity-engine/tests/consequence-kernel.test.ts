import { test } from "node:test";
import assert from "node:assert/strict";
import {
  allocateResource,
  executeDecision,
  proposeDecision,
  replayOutcome,
} from "../src/crk1/consequence-kernel";
import { InMemoryConsequenceLedger } from "../src/crk1/consequence-ledger";
import {
  validateConsequenceChain,
  validateK01,
  validateObjectK11,
  validateTransitionK11,
} from "../src/crk1/consequence-invariants";
import {
  detectInsulatedDecisions,
  proveAntiInsulation,
  K3_PROOF_STEPS,
} from "../src/crk1/anti-insulation";
import { runConsequencePipeline } from "../src/crk1/consequence-pipeline";

const identity = {
  id: "id-steward-1",
  lineageId: "lineage-alpha",
  timestamp: "2026-06-19T00:00:00.000Z",
};

const evidence = {
  id: "ev-initial",
  timestamp: "2026-06-19T00:00:00.000Z",
  payload: { signal: "latency_p99", value: 120 },
  admissible: true,
};

test("K0: propose → allocate → execute → replay yields valid chain", async () => {
  const ledger = new InMemoryConsequenceLedger();
  const result = await runConsequencePipeline(ledger, {
    identity,
    evidence: [evidence],
    outcomePayload: { latency: 130 },
  });

  assert.equal(result.validation.valid, true);
  assert.equal(result.antiInsulation.constitutionallyValid, true);
  assert.ok(result.evidenceId);
});

test("K0.1 rejects executed decision without outcome", async () => {
  const ledger = new InMemoryConsequenceLedger();
  await ledger.putIdentity(identity);
  await ledger.putDecision({
    id: "dec-bad",
    identityId: identity.id,
    evidenceIds: [evidence.id],
    timestamp: "2026-06-19T00:00:00.000Z",
    payload: {},
    committed: true,
    executed: true,
  });

  const k0 = await validateK01(ledger, "dec-bad");
  assert.equal(k0.valid, false);
  assert.ok(k0.violations.some((v) => v.code === "K0.NO_OUTCOME"));
});

test("K1 blocks non-replayable outcome at execution", () => {
  const { decision } = proposeDecision({ identity, evidence: [evidence] });
  const { resource } = allocateResource({
    decision,
    resource: { id: "res-1", payload: {} },
  });

  assert.throws(
    () =>
      executeDecision({
        decision,
        resource,
        outcome: { id: "out-1", payload: {}, replayable: false },
      }),
    /K1/,
  );
});

test("K1 blocks inadmissible evidence on propose", () => {
  assert.throws(
    () =>
      proposeDecision({
        identity,
        evidence: [{ ...evidence, id: "ev-bad", admissible: false }],
      }),
    /K1/,
  );
});

test("K1 transition severability — execute without outcome output", () => {
  const result = validateTransitionK11({
    id: "tx-bad",
    kind: "execute_decision",
    timestamp: "2026-06-19T00:00:00.000Z",
    inputIds: { decision: "d1", resource: "r1" },
    outputIds: {},
  });
  assert.equal(result.valid, false);
  assert.equal(result.violations[0]!.law, "K1");
});

test("K1 object check flags quarantined evidence", () => {
  const result = validateObjectK11({
    evidence: { ...evidence, admissible: false },
  });
  assert.equal(result.valid, false);
  assert.ok(result.violations.some((v) => v.code === "K1.QUARANTINED_EVIDENCE"));
});

test("K2 detects missing lineage binding on replayed evidence", async () => {
  const ledger = new InMemoryConsequenceLedger();
  await ledger.putIdentity(identity);
  await ledger.putEvidence(evidence);

  const { decision } = proposeDecision({ identity, evidence: [evidence] });
  await ledger.putDecision({ ...decision, executed: true });

  const outcome = {
    id: "out-1",
    decisionId: decision.id,
    resourceId: "res-1",
    timestamp: "2026-06-19T00:00:00.000Z",
    payload: { result: "done" },
    replayable: true,
  };
  await ledger.putOutcome(outcome);

  await ledger.putEvidence({
    id: "ev-replay-wrong-lineage",
    timestamp: "2026-06-19T01:00:00.000Z",
    payload: {},
    sourceOutcomeId: outcome.id,
    admissible: true,
    affectsLineageId: "other-lineage",
  });

  const k2 = await validateConsequenceChain(ledger, identity, decision.id);
  assert.equal(k2.valid, false);
  assert.ok(k2.violations.some((v) => v.code === "K2.NO_LINEAGE_BINDING"));
});

test("K3 detects insulated state when consequences cannot reach judgment", async () => {
  const ledger = new InMemoryConsequenceLedger();
  await ledger.putIdentity(identity);
  await ledger.putEvidence(evidence);

  const { decision } = proposeDecision({ identity, evidence: [evidence] });
  await ledger.putDecision({ ...decision, executed: true });
  await ledger.putOutcome({
    id: "out-insulated",
    decisionId: decision.id,
    resourceId: "res-1",
    timestamp: "2026-06-19T00:00:00.000Z",
    payload: {},
    replayable: true,
  });
  // No replay evidence — insulated

  const insulated = await detectInsulatedDecisions(ledger, identity);
  assert.equal(insulated.length, 1);

  const proof = await proveAntiInsulation(ledger, identity);
  assert.equal(proof.constitutionallyValid, false);
  assert.ok(proof.violations.length > 0);
});

test("K3 proof steps are documented", () => {
  assert.equal(K3_PROOF_STEPS.length, 5);
  assert.ok(K3_PROOF_STEPS[4]!.includes("outside the constitutional runtime"));
});

test("replayOutcome binds evidence to lineage", () => {
  const outcome = {
    id: "out-1",
    decisionId: "dec-1",
    resourceId: "res-1",
    timestamp: "2026-06-19T00:00:00.000Z",
    payload: { value: 42 },
    replayable: true,
  };

  const { evidence: replayed } = replayOutcome({
    outcome,
    affectsLineageId: identity.lineageId,
    evidence: { id: "ev-r", payload: {} },
  });

  assert.equal(replayed.affectsLineageId, identity.lineageId);
  assert.equal(replayed.admissible, true);
  assert.equal(replayed.sourceOutcomeId, outcome.id);
});
