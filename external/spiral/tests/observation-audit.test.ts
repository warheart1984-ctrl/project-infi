import assert from "node:assert/strict";
import test from "node:test";
import {
  buildObservationAuditSummary,
  isObservationAuditDue,
} from "../server/evolution-cycle";
import {
  parseObservationAuditSummary,
  resolveObservationAuditGate,
} from "../server/lib/observation-audit-policy";

test("observation audit summary remains deterministic", () => {
  const summary = buildObservationAuditSummary({
    gatesFailed: 1,
    mimicryFindings: 2,
    firstGateFailureId: "inspection-dispatch-precedes-recall",
    firstMimicryClass: "surface-echo",
  });

  assert.equal(
    summary,
    "Observation audit: gatesFailed=1 mimicryFindings=2 firstGateFailure=inspection-dispatch-precedes-recall firstMimicry=surface-echo",
  );
});

test("observation audit cadence returns due only after interval", () => {
  assert.equal(isObservationAuditDue(0, 1000, 60000), true);
  assert.equal(isObservationAuditDue(50_000, 100_000, 60_000), false);
  assert.equal(isObservationAuditDue(39_000, 100_000, 60_000), true);
});

test("observation audit summary parser extracts bounded counters", () => {
  assert.deepEqual(
    parseObservationAuditSummary(
      "Observation audit: gatesFailed=1 mimicryFindings=2 firstGateFailure=x firstMimicry=surface-echo",
    ),
    { gatesFailed: 1, mimicryFindings: 2 },
  );
});

test("observation audit gate only seals on fresh failing audits", () => {
  assert.deepEqual(
    resolveObservationAuditGate(
      {
        lastObservationAuditAt: 100_000,
        lastObservationAuditSummary: "Observation audit: gatesFailed=0 mimicryFindings=0",
      },
      100_500,
    ),
    { active: false, gatesFailed: 0, mimicryFindings: 0 },
  );

  assert.deepEqual(
    resolveObservationAuditGate(
      {
        lastObservationAuditAt: 100_000,
        lastObservationAuditSummary: "Observation audit: gatesFailed=1 mimicryFindings=0",
      },
      100_500,
    ),
    {
      active: true,
      reason: "observation-audit-gates",
      gatesFailed: 1,
      mimicryFindings: 0,
    },
  );

  assert.deepEqual(
    resolveObservationAuditGate(
      {
        lastObservationAuditAt: 1,
        lastObservationAuditSummary: "Observation audit: gatesFailed=0 mimicryFindings=1",
      },
      2_000_000,
    ),
    { active: false, gatesFailed: 0, mimicryFindings: 1 },
  );
});
