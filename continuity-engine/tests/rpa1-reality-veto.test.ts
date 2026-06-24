import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  RPA1_PRINCIPLES,
  buildMandatoryReconsiderationCycle,
  detectRealityDivergence,
  escalateIgnoredVeto,
  issueRealityVeto,
  InMemoryRealityVetoLedger,
} from "../src/index.js";

describe("RPA-1 Reality Veto", () => {
  it("exports constitutional principles", () => {
    assert.ok(RPA1_PRINCIPLES.RPA_1_1.includes("final arbiter"));
    assert.ok(RPA1_PRINCIPLES.RPA_1_2.includes("evidence"));
  });

  it("RV-1 detects divergence beyond tolerance", () => {
    assert.equal(
      detectRealityDivergence({ expected: 100, observed: 100, evidence: {} }),
      false,
    );
    assert.equal(
      detectRealityDivergence({ expected: 100, observed: 150, evidence: { id: "ev-1" } }),
      true,
    );
  });

  it("RV-2 issues veto receipt when evidence contradicts expectation", () => {
    const receipt = issueRealityVeto({
      expected: { threshold: 0.6, metric: "accuracy" },
      observed: { threshold: 0.4, metric: "accuracy" },
      evidence: { observations: [1, 2, 3] },
      observerId: "steward-1",
      timestamp: "2026-06-24T00:00:00.000Z",
    });
    assert.ok(receipt);
    assert.equal(receipt!.observerId, "steward-1");
    assert.ok(["minor", "major", "critical"].includes(receipt!.severity));
  });

  it("RV-3 builds mandatory reconsideration cycle", () => {
    const receipt = issueRealityVeto({
      expected: 1,
      observed: 0,
      evidence: { signal: "mismatch" },
      timestamp: "2026-06-24T00:00:00.000Z",
    })!;
    const cycle = buildMandatoryReconsiderationCycle(receipt);
    assert.equal(cycle.corrigibilityStatus, "sound");
    assert.ok(cycle.tags?.includes("reality-veto"));
    assert.equal((cycle.context as { mandatory: boolean }).mandatory, true);
  });

  it("RV-4 escalates ignored or suppressed veto", () => {
    const receipt = issueRealityVeto({
      expected: 10,
      observed: 0,
      evidence: { signal: "critical mismatch" },
      observerId: "steward-1",
    });
    assert.ok(receipt);

    const escalation = escalateIgnoredVeto(receipt!, { ignored: true });
    assert.equal(escalation.judgmentIllegitimate, true);
    assert.equal(escalation.blockThresholdChanges, true);
    assert.equal(escalation.stewardLineageAtRisk, true);

    const suppressed = escalateIgnoredVeto(
      { ...receipt!, suppressed: true, severity: "critical" },
      { suppressed: true },
    );
    assert.equal(suppressed.lineageCorrigibilityFailed, true);
  });

  it("stores veto receipts in continuity ledger", () => {
    const ledger = new InMemoryRealityVetoLedger();
    const receipt = issueRealityVeto({
      expected: 5,
      observed: 10,
      evidence: { x: 1 },
      observerId: "obs-1",
    })!;
    ledger.append(receipt);
    assert.equal(ledger.queryByObserver("obs-1").length, 1);
  });
});
