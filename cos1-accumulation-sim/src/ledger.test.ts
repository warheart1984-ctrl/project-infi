import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { deriveRecalibrationViews, deriveThresholdViews } from "./ledger/views.js";
import type { JudgmentCycle } from "./judgment/types.js";

function cycleWithDecision(
  id: string,
  observerId: string,
  decision: Record<string, unknown>,
): JudgmentCycle {
  const empty = { summary: "", eventIds: [] };
  return {
    id,
    observerId,
    timestamp: "2026-06-23T22:00:00Z",
    observation: empty,
    interpretation: empty,
    valuation: empty,
    decision,
    context: { domain: "governance" },
    outcome: empty,
    feedback: empty,
    reflection: empty,
  };
}

describe("Continuity Ledger v2 views", () => {
  it("derives threshold views from threshold_adoption cycles", () => {
    const cycles = [
      cycleWithDecision("JC-T1", "Mod", {
        type: "threshold_adoption",
        thresholdId: "MAT-3",
        domain: "CSS-2",
        metric: "laCompounding",
        comparator: ">=",
        value: 3,
      }),
      cycleWithDecision("JC-T2", "Mod", {
        type: "threshold_adoption",
        thresholdId: "MAT-3",
        domain: "CSS-2",
        metric: "laCompounding",
        comparator: ">=",
        value: 4,
      }),
    ];
    cycles[1] = { ...cycles[1]!, timestamp: "2026-06-23T23:00:00Z" };
    const views = deriveThresholdViews(cycles);
    assert.equal(views.length, 1);
    assert.equal(views[0]?.id, "MAT-3");
    assert.equal(views[0]?.value, 4);
    assert.deepEqual(views[0]?.supportingCycleIds, ["JC-T1", "JC-T2"]);
  });

  it("derives recalibration views linked to source cycle", () => {
    const cycles = [
      cycleWithDecision("JC-R1", "Sue", {
        type: "threshold_recalibration",
        thresholdId: "MAT-3",
        fromValue: 3,
        toValue: 5,
      }),
    ];
    const views = deriveRecalibrationViews(cycles, "MAT-3");
    assert.equal(views.length, 1);
    assert.equal(views[0]?.cycleId, "JC-R1");
    assert.equal(views[0]?.fromValue, 3);
    assert.equal(views[0]?.toValue, 5);
  });
});
