import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { computeStewardScore, evaluateStewardPromotion } from "./stewardship.js";
import { evaluateQuestCondition } from "./quest.js";
import { defaultConstitution } from "./constitution.js";
import {
  gameEventToContribution,
  toContinuityHealthResponse,
} from "./gosAdapter.js";
import {
  initialWorldRuntime,
  ingestGameEvent,
  proposeWorldChange,
  getWorldHistory,
  getContinuityHealth,
} from "./worldState.js";
import { applyEvent, initialState } from "./state.js";
import { classifyOrigin } from "./originClassifier.js";
import { classifyMode } from "./epistemicClassifier.js";
import { proposalToLineageChange } from "./changeAdapter.js";
import { gameEventToJPSS } from "./gameAdapter.js";

describe("epistemicClassifier", () => {
  it("defaults accumulation events to INTERPRETATION", () => {
    assert.equal(
      classifyMode({ accumulationType: "A2", fromExposure: false }),
      "INTERPRETATION",
    );
  });

  it("classifies raw NONE events as OBSERVATION", () => {
    assert.equal(
      classifyMode({ accumulationType: "NONE", fromExposure: false }),
      "OBSERVATION",
    );
  });
});

describe("originClassifier", () => {
  it("classifies by exposure and accumulation type", () => {
    assert.equal(classifyOrigin({ fromExposure: false, accumulationType: "A2" }), "PLA");
    assert.equal(classifyOrigin({ fromExposure: true, accumulationType: "A1" }), "LA");
    assert.equal(classifyOrigin({ fromExposure: true, accumulationType: "A3" }), "SA");
  });
});

describe("changeAdapter", () => {
  it("maps proposal to provisional lineage change with origin", () => {
    const change = proposalToLineageChange({
      id: "WC-1",
      description: "Cap magic",
      proposedBy: "p1",
      origin: "LA",
      affectsSystems: ["magic"],
      hypothesis: {
        expectedEffects: ["less drift"],
        metrics: ["aggregatePSD"],
        validationWindowDays: 7,
      },
    });
    assert.equal(change.status, "PROVISIONAL");
    assert.equal(change.originType, "LA");
  });
});

describe("gameAdapter", () => {
  it("classifies DISCOVER_MECHANIC as A1 Mechanics", () => {
    const jpss = gameEventToJPSS({
      id: "E1",
      actorId: "player-42",
      timestamp: "2026-06-23T22:00:00Z",
      type: "ACTION",
      action: "DISCOVER_MECHANIC",
      context: { locationId: "zone-7" },
    });
    assert.equal(jpss.accumulationType, "A1");
    assert.equal(jpss.targetsLayer, "Continuity");
    assert.equal(jpss.fromExposure, false);
  });

  it("classifies GOVERNANCE as A2 Politics", () => {
    const jpss = gameEventToJPSS({
      id: "G1",
      actorId: "mod-1",
      timestamp: "2026-06-23T22:00:00Z",
      type: "GOVERNANCE",
      action: "VALIDATE_RULE",
      context: {},
    });
    assert.equal(jpss.accumulationType, "A2");
    assert.equal(jpss.targetsLayer, "Governance");
  });

  it("applyEvent tags origin on ingest", () => {
    let state = initialState();
    state = applyEvent(
      state,
      gameEventToJPSS({
        id: "E1",
        actorId: "player-42",
        timestamp: "2026-06-23T22:00:00Z",
        type: "ACTION",
        action: "DISCOVER_MECHANIC",
        context: { locationId: "zone-7" },
      }),
    );
    assert.equal(state.events[0]?.origin, "PLA");
  });
});

describe("GOS-1 / WCK-1", () => {
  it("ingests game events into continuity kernel", () => {
    let world = initialWorldRuntime();
    world = ingestGameEvent(world, {
      id: "G1",
      actorId: "player-1",
      timestamp: new Date().toISOString(),
      type: "ACTION",
      action: "observe_drift",
      context: {
        fromExposure: false,
        phenomenonAnchor: "magic instability",
        accumulationTag: {
          origin: "PLA",
          accumulationType: "A2",
          targetsLayer: "Mechanics",
          buildsOn: [],
        },
      },
    });
    assert.equal(world.kernel.events.at(-1)?.origin, "PLA");
    assert.equal(world.kernel.events.at(-1)?.mode, "OBSERVATION");
    assert.equal(world.players["player-1"]?.plaCount, 1);
  });

  it("GET continuity health shape", () => {
    const health = getContinuityHealth(initialWorldRuntime());
    assert.ok("PLA" in health.accumulation);
    assert.ok("LA" in health.accumulation);
    assert.ok("SA" in health.accumulation);
    assert.equal(typeof health.mat3, "boolean");
  });

  it("proposes and lists world changes", () => {
    let world = initialWorldRuntime();
    world = proposeWorldChange(world, {
      id: "WC-1",
      description: "Cap spell amplification",
      proposedBy: "player-1",
      origin: "LA",
      affectsSystems: ["magic"],
      hypothesis: {
        expectedEffects: ["Reduced drift"],
        metrics: ["aggregatePSD"],
        validationWindowDays: 7,
      },
    });
    assert.equal(world.worldChanges["WC-1"]?.status, "PROVISIONAL");
    assert.ok(world.kernel.events.some((e) => e.mode === "INTEGRATION"));
    assert.equal(getWorldHistory(world, "PROVISIONAL").length, 1);
  });

  it("world constitution has K1-K4 invariants", () => {
    const c = defaultConstitution();
    assert.equal(c.invariants.length, 4);
    assert.ok(c.amendmentRules.some((r) => r.requiredRoles.includes("STEWARD")));
  });
});

describe("Stewardship promotion", () => {
  it("promotes player at threshold", () => {
    const player = {
      id: "p1",
      name: "Alex",
      plaCount: 2,
      laCount: 3,
      saCount: 1,
      reconstructabilityScore: 0.9,
      stewardshipScore: 0,
      roles: ["CITIZEN"],
    };
    const promoted = evaluateStewardPromotion(player, {
      plaDepth: 0.8,
      laDepth: 0.7,
      saEvidence: 0.6,
      reconstructability: 0.9,
      validationRate: 0.8,
      driftImpact: 0.1,
    });
    assert.ok(promoted.roles.includes("STEWARD"));
    assert.ok(promoted.stewardshipScore >= 0.7);
  });

  it("computeStewardScore penalizes drift", () => {
    const low = computeStewardScore({
      plaDepth: 0.5,
      laDepth: 0.5,
      saEvidence: 0.5,
      reconstructability: 0.5,
      validationRate: 0.5,
      driftImpact: 0.1,
    });
    const high = computeStewardScore({
      plaDepth: 0.5,
      laDepth: 0.5,
      saEvidence: 0.5,
      reconstructability: 0.5,
      validationRate: 0.5,
      driftImpact: 0.9,
    });
    assert.ok(low > high);
  });
});

describe("Quest DSL", () => {
  it("evaluates drift quest condition", () => {
    const hit = evaluateQuestCondition(
      "drift.aggregatePSD > 0.6 && affectsSystems.includes('magic')",
      {
        driftAggregatePSD: 0.75,
        affectsSystems: ["magic"],
        hasProvisionalChange: false,
        hasValidatedChange: false,
        stewardEmergence: false,
      },
    );
    assert.equal(hit, true);
  });
});

describe("GOS adapter", () => {
  it("maps world layer Mechanics to Continuity", () => {
    const ev = gameEventToContribution({
      id: "E1",
      actorId: "Jon",
      timestamp: "2026-06-23T22:00:00Z",
      type: "ACTION",
      action: "test",
      context: {
        fromExposure: false,
        phenomenonAnchor: "drift",
        accumulationTag: {
          origin: "PLA",
          accumulationType: "A2",
          targetsLayer: "Mechanics",
          buildsOn: [],
        },
      },
    });
    assert.equal(ev.targetsLayer, "Continuity");
  });

  it("toContinuityHealthResponse from kernel", () => {
    let kernel = initialState();
    kernel = applyEvent(kernel, {
      id: "E1",
      actor: "Jon",
      timestamp: "2026-06-23T22:00:00Z",
      accumulationType: "A2",
      targetsLayer: "Continuity",
      fromExposure: false,
      buildsOn: [],
      phenomenonAnchor: "drift",
    });
    assert.equal(kernel.events[0]?.origin, "PLA");
    assert.equal(kernel.events[0]?.mode, "INTERPRETATION");
    const health = toContinuityHealthResponse(kernel);
    assert.equal(health.accumulation.PLA.count, 1);
    assert.equal(health.epistemic.interpretationCount, 1);
    assert.equal(typeof health.pla.instrumentality, "number");
  });
});
