import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { applyEvent, initialState, applyJudgmentCycle } from "./state.js";
import { withEventTags } from "./epistemicClassifier.js";
import { rebuildCyclesFromEvents, allCyclesForAnalytics } from "./judgment/cycleAssembly.js";
import { inferCapabilityProfile } from "./judgment/analytics/capability.js";
import { evaluateJudgmentFromCycles } from "./judgment/analytics/evaluation.js";
import { assessJudgmentLegitimacy } from "./governance/judgment-governance.js";
import { evaluateThresholdDeltaWithJudgment } from "./governance/governance-engine.js";
import { createEmptyDraft } from "./judgment/payload.js";
import type { JudgmentCycle } from "./judgment/types.js";

function completeCycle(
  id: string,
  observerId: string,
  timestamp: string,
): JudgmentCycle {
  const base = createEmptyDraft(id, observerId, timestamp);
  return {
    id: base.id,
    observerId: base.observerId,
    timestamp: base.timestamp,
    observation: {
      summary: "saw drift",
      eventIds: ["O1"],
      timestamp,
      phenomenonAnchor: "drift",
      origin: "PLA",
      fromExposure: false,
    },
    interpretation: {
      summary: "pattern",
      eventIds: ["I1"],
      timestamp,
      accumulationType: "A2",
      targetsLayer: "Continuity",
    },
    valuation: { summary: "layer", eventIds: ["I1"], timestamp },
    decision: { summary: "commit", eventIds: ["C1"], timestamp },
    context: { summary: "ctx", eventIds: [], timestamp, buildsOn: ["O1"] },
    outcome: { summary: "ok", eventIds: ["V1"], timestamp },
    feedback: { summary: "signals", eventIds: ["V1"], timestamp, validationMode: true },
    reflection: { summary: "recalibrate", eventIds: ["V1"], timestamp },
    relatedThresholdIds: [],
    relatedDeltaIds: [],
    tags: [],
  };
}

describe("JudgmentCycle (RA-COS-1 primitive)", () => {
  it("assembles a complete cycle from event stream into ledger", () => {
    const events = [
      withEventTags({
        id: "O1",
        actor: "Jon",
        timestamp: "2026-06-23T22:00:00Z",
        accumulationType: "NONE",
        targetsLayer: "Continuity",
        fromExposure: false,
        buildsOn: [],
        phenomenonAnchor: "calibration drift",
        mode: "OBSERVATION",
      }),
      withEventTags({
        id: "I1",
        actor: "Jon",
        timestamp: "2026-06-23T22:05:00Z",
        accumulationType: "A2",
        targetsLayer: "Continuity",
        fromExposure: false,
        buildsOn: ["O1"],
        mode: "INTERPRETATION",
      }),
      withEventTags({
        id: "C1",
        actor: "Jon",
        timestamp: "2026-06-23T22:10:00Z",
        accumulationType: "A2",
        targetsLayer: "Governance",
        fromExposure: true,
        buildsOn: ["WC-1"],
        mode: "INTEGRATION",
      }),
      withEventTags({
        id: "V1",
        actor: "Jon",
        timestamp: "2026-06-23T22:15:00Z",
        accumulationType: "A1",
        targetsLayer: "Meta",
        fromExposure: true,
        buildsOn: ["WC-1"],
        mode: "VALIDATION",
      }),
    ];
    const { ledgerCycles, drafts } = rebuildCyclesFromEvents(events);
    assert.equal(ledgerCycles.length, 1);
    assert.equal(drafts.length, 0);
    assert.ok(ledgerCycles[0]?.observation);
    assert.ok(ledgerCycles[0]?.reflection);
  });

  it("applyEvent stores open drafts and infers capability as hypothesis", () => {
    let state = initialState();
    for (const ev of [
      {
        id: "O1",
        actor: "Sue",
        timestamp: "2026-06-23T22:00:00Z",
        accumulationType: "NONE" as const,
        targetsLayer: "Continuity",
        fromExposure: false,
        buildsOn: [] as string[],
        phenomenonAnchor: "drift",
        mode: "OBSERVATION" as const,
      },
      {
        id: "I1",
        actor: "Sue",
        timestamp: "2026-06-23T22:05:00Z",
        accumulationType: "A2" as const,
        targetsLayer: "Continuity",
        fromExposure: false,
        buildsOn: ["O1"],
        mode: "INTERPRETATION" as const,
      },
    ]) {
      state = applyEvent(state, ev);
    }
    assert.equal(state.ledgerCycles.length, 0);
    assert.equal(state.cycleDrafts.length, 1);
    assert.ok(state.capabilityProfiles["Sue"]);
    const all = allCyclesForAnalytics(state.ledgerCycles, state.cycleDrafts);
    const eval_ = evaluateJudgmentFromCycles(all, "Sue");
    assert.equal(eval_.isHypothesis, true);
    assert.ok(eval_.score > 0);
  });
});

describe("Judgment analytics", () => {
  it("capability profile cites evidence cycle ids", () => {
    const cycle = completeCycle("JC1", "Alex", "2026-06-23T22:00:00Z");
    const profile = inferCapabilityProfile([cycle], "Alex");
    assert.deepEqual(profile.evidenceCycles, ["JC1"]);
    assert.ok(profile.score > 0);
  });
});

describe("Governance (cycles + JPA-1)", () => {
  it("rejects delta when no cycle evidence for actor", () => {
    const result = evaluateThresholdDeltaWithJudgment({
      delta: {
        id: "TD-1",
        thresholdId: "MAT-3",
        fromVersion: 1,
        toVersion: 2,
        proposedBy: "unknown",
        description: "raise bar",
        affectsInvariants: ["K3"],
      },
      invariants: { ids: ["K3"], weights: { K3: 0.5 } },
      judgmentContext: { actorId: "unknown", cycles: [] },
    });
    assert.equal(result.allowed, false);
    assert.ok(result.reasons.some((r) => r.includes("JPA-1")));
  });

  it("assessJudgmentLegitimacy uses cycles not raw vectors", () => {
    let state = initialState();
    state = applyJudgmentCycle(state, completeCycle("JC-full", "Mod", "2026-06-23T22:00:00Z"));

    const legitimacy = assessJudgmentLegitimacy({
      actorId: "Mod",
      cycles: state.ledgerCycles,
    });
    assert.equal(legitimacy.evaluation.isHypothesis, true);
    assert.ok(legitimacy.evaluation.evidenceCycleCount >= 1);
  });
});
