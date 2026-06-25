import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { validateVAS1, computeContinuityMetrics, computeEpistemicMetrics, computePLAQualityMetrics, computeInstrumentalityIndex } from "./engine.js";
import { applyEvent, initialState, runPostAcceptanceValidation, registerChange } from "./state.js";
import type { JPSSContributionEvent } from "./domain.js";
import { withEventTags } from "./epistemicClassifier.js";
import {
  classifyAccumulationOrigin,
  evaluatePLACriteria,
  isPLAEvent,
} from "./pla.js";

describe("RA-COS-1 engine", () => {
  it("validateVAS1 requires three of five criteria", () => {
    const weak = validateVAS1({
      predictiveAccuracyDelta: 0,
      explanatoryCompressionDelta: 0,
      crossDomainConvergence: 0,
      operationalOutcomeDelta: 0,
      critiqueStability: 0,
    });
    assert.equal(weak.passed, false);

    const strong = validateVAS1({
      predictiveAccuracyDelta: 0.1,
      explanatoryCompressionDelta: 0.05,
      crossDomainConvergence: 0.7,
      operationalOutcomeDelta: 0.1,
      critiqueStability: 0.6,
    });
    assert.equal(strong.passed, true);
    assert.ok(strong.criteriaPassed.length >= 3);
  });

  it("CSS-2 MAT-3 requires LA compounding only", () => {
    const events: JPSSContributionEvent[] = [
      withEventTags({
        id: "E1",
        actor: "Jon",
        timestamp: "2026-06-23T22:00:00Z",
        accumulationType: "A2",
        targetsLayer: "Continuity",
        fromExposure: false,
        buildsOn: [],
        phenomenonAnchor: "calibration drift",
      }),
      withEventTags({
        id: "E2",
        actor: "Sue",
        timestamp: "2026-06-23T22:05:00Z",
        accumulationType: "A1",
        targetsLayer: "Continuity",
        fromExposure: true,
        buildsOn: ["E1"],
      }),
      withEventTags({
        id: "E3",
        actor: "Bradley",
        timestamp: "2026-06-23T22:10:00Z",
        accumulationType: "A2",
        targetsLayer: "Transferability",
        fromExposure: true,
        buildsOn: ["E1"],
      }),
    ];
    const metrics = computeContinuityMetrics(events, null);
    assert.equal(metrics.accumulationCount, 3);
    assert.equal(metrics.mat3, false);
    assert.equal(metrics.pla.plaCount, 1);
    assert.equal(metrics.la.laCount, 2);
  });

  it("MAT-3 passes with three LA events from two actors", () => {
    const base: JPSSContributionEvent[] = [
      withEventTags({
        id: "E1",
        actor: "Jon",
        timestamp: "2026-06-23T22:00:00Z",
        accumulationType: "A2",
        targetsLayer: "Continuity",
        fromExposure: false,
        buildsOn: [],
        phenomenonAnchor: "drift",
      }),
      withEventTags({
        id: "E2",
        actor: "Sue",
        timestamp: "2026-06-23T22:05:00Z",
        accumulationType: "A2",
        targetsLayer: "Continuity",
        fromExposure: true,
        buildsOn: ["E1"],
      }),
      withEventTags({
        id: "E3",
        actor: "Bradley",
        timestamp: "2026-06-23T22:10:00Z",
        accumulationType: "A2",
        targetsLayer: "Transferability",
        fromExposure: true,
        buildsOn: ["E1"],
      }),
      withEventTags({
        id: "E4",
        actor: "Sue",
        timestamp: "2026-06-23T22:15:00Z",
        accumulationType: "A2",
        targetsLayer: "Transferability",
        fromExposure: true,
        buildsOn: ["E2"],
      }),
    ];
    const metrics = computeContinuityMetrics(base, null);
    assert.equal(metrics.la.laCount, 3);
    assert.equal(metrics.mat3, true);
  });

  it("runPostAcceptanceValidation records originType on ledger", () => {
    let state = initialState();
    state = registerChange(state, {
      id: "chg-1",
      description: "PLA-originated patch",
      affectsInvariants: ["K4"],
      status: "PROVISIONAL",
      acceptedAt: new Date().toISOString(),
      validatedAt: null,
      originType: "PLA",
    });
    state = {
      ...state,
      consequences: [
        {
          changeId: "chg-1",
          timestamp: new Date().toISOString(),
          metric: "predictiveAccuracy",
          value: 0.8,
        },
        {
          changeId: "chg-1",
          timestamp: new Date().toISOString(),
          metric: "operationalOutcome",
          value: 0.7,
        },
      ],
    };
    state = runPostAcceptanceValidation(
      state,
      "chg-1",
      {
        predictiveAccuracyDelta: 0.1,
        explanatoryCompressionDelta: 0.05,
        crossDomainConvergence: 0.7,
        operationalOutcomeDelta: 0.1,
        critiqueStability: 0.6,
      },
      0.5,
    );
    assert.equal(state.changes["chg-1"]?.status, "VALIDATED");
    assert.equal(state.ledger["chg-1"]?.originType, "PLA");
    assert.ok(state.events.some((e) => e.mode === "INTEGRATION"));
    assert.ok(state.events.some((e) => e.mode === "VALIDATION"));
  });

  it("computeEpistemicMetrics tracks O/I/I₂/V counts and profile", () => {
    const events = [
      withEventTags({
        id: "O1",
        actor: "Jon",
        timestamp: "2026-06-23T22:00:00Z",
        accumulationType: "NONE",
        targetsLayer: "Continuity",
        fromExposure: false,
        buildsOn: [],
        mode: "OBSERVATION",
      }),
      withEventTags({
        id: "I1",
        actor: "Sue",
        timestamp: "2026-06-23T22:05:00Z",
        accumulationType: "A1",
        targetsLayer: "Continuity",
        fromExposure: true,
        buildsOn: ["O1"],
        mode: "INTERPRETATION",
      }),
      withEventTags({
        id: "I2",
        actor: "Bradley",
        timestamp: "2026-06-23T22:10:00Z",
        accumulationType: "A2",
        targetsLayer: "Transferability",
        fromExposure: true,
        buildsOn: ["O1"],
        mode: "INTERPRETATION",
      }),
    ];
    const epistemic = computeEpistemicMetrics(events);
    assert.equal(epistemic.observationCount, 1);
    assert.equal(epistemic.interpretationCount, 2);
    assert.equal(epistemic.externalObservationCount, 1);
    assert.equal(epistemic.profile, "framework");
  });

  it("computePLAQualityMetrics measures clustering and instrumentality", () => {
    const events = [
      withEventTags({
        id: "P1",
        actor: "Jon",
        timestamp: "2026-06-23T22:00:00Z",
        accumulationType: "A2",
        targetsLayer: "Continuity",
        fromExposure: false,
        buildsOn: ["WC-1"],
        phenomenonAnchor: "drift",
      }),
      withEventTags({
        id: "P2",
        actor: "Sue",
        timestamp: "2026-06-23T22:05:00Z",
        accumulationType: "A2",
        targetsLayer: "Continuity",
        fromExposure: false,
        buildsOn: [],
        phenomenonAnchor: "drift",
      }),
      withEventTags({
        id: "P3",
        actor: "Bradley",
        timestamp: "2026-06-23T22:10:00Z",
        accumulationType: "A2",
        targetsLayer: "Transferability",
        fromExposure: false,
        buildsOn: [],
        phenomenonAnchor: "transfer",
      }),
    ];
    const ledger = {
      "WC-1": {
        changeId: "WC-1",
        originType: "PLA" as const,
        surpassmentEvidence: "",
        acceptanceEvidence: "",
        validationResult: "PASSED" as const,
        driftSignals: null,
        finalStatus: "VALIDATED" as const,
        notes: [],
      },
    };
    const quality = computePLAQualityMetrics(events, ledger);
    assert.equal(quality.clustering, 2 / 3);
    assert.equal(quality.crossDomainRecurrence, 2 / 3);
    assert.equal(quality.validationSurvival, 1);
    const instrumentality = computeInstrumentalityIndex(quality);
    assert.ok(instrumentality > 0.5);
    const metrics = computeContinuityMetrics(events, null, undefined, false, ledger);
    assert.equal(metrics.pla.instrumentality, instrumentality);
  });
});

describe("RA-COS-1 state", () => {
  it("applyEvent updates continuity and epistemic mode", () => {
    let state = initialState();
    state = applyEvent(state, {
      id: "E_JON_A2",
      actor: "Jon",
      timestamp: "2026-06-23T22:00:00Z",
      accumulationType: "A2",
      targetsLayer: "Continuity",
      fromExposure: false,
      buildsOn: [],
      phenomenonAnchor: "calibration drift",
    });
    assert.equal(state.continuity.accumulationCount, 1);
    assert.equal(state.continuity.mat3, false);
    assert.equal(state.eventOrigins["E_JON_A2"], "PLA");
    assert.equal(state.continuity.pla.plaCount, 1);
    assert.equal(state.events[0]?.origin, "PLA");
    assert.equal(state.events[0]?.mode, "INTERPRETATION");
    assert.equal(state.continuity.epistemic.interpretationCount, 1);
  });
});

describe("PLA-1 / CSS-2", () => {
  const jonPla = withEventTags({
    id: "E_JON_A2",
    actor: "Jon",
    timestamp: "2026-06-23T22:00:00Z",
    accumulationType: "A2",
    targetsLayer: "Continuity",
    fromExposure: false,
    buildsOn: [],
    phenomenonAnchor: "calibration drift",
  });

  const sueLa = withEventTags({
    id: "E_SUE_A1",
    actor: "Sue",
    timestamp: "2026-06-23T22:05:00Z",
    accumulationType: "A1",
    targetsLayer: "Continuity",
    fromExposure: true,
    buildsOn: ["E_JON_A2"],
  });

  it("classifies Jon as PLA and Sue as LA via origin field", () => {
    assert.equal(jonPla.origin, "PLA");
    assert.equal(sueLa.origin, "LA");
    assert.equal(classifyAccumulationOrigin(jonPla), "PLA");
    assert.equal(classifyAccumulationOrigin(sueLa), "LA");
  });

  it("requires all four PLA criteria", () => {
    const criteria = evaluatePLACriteria(jonPla);
    assert.equal(criteria.noFrameworkExposure, true);
    assert.equal(criteria.phenomenonAnchored, true);
    assert.equal(criteria.lineageCompatible, true);
    assert.equal(criteria.explanatoryGain, true);
    assert.equal(isPLAEvent(jonPla), true);

    const noAnchor = { ...jonPla, phenomenonAnchor: null };
    assert.equal(isPLAEvent(noAnchor), false);
  });

  it("computes integration and listening interpretation on Jon/Sue/Bradley log", () => {
    const bradleyLa = withEventTags({
      id: "E_BRADLEY_A2",
      actor: "Bradley",
      timestamp: "2026-06-23T22:10:00Z",
      accumulationType: "A2",
      targetsLayer: "Transferability",
      fromExposure: true,
      buildsOn: ["E_JON_A2"],
    });
    const events = [jonPla, sueLa, bradleyLa];
    let state = initialState();
    for (const ev of events) state = applyEvent(state, ev);

    assert.equal(state.continuity.pla.plaCount, 1);
    assert.equal(state.continuity.pla.plaToLaIntegrationRate, 1);
    assert.equal(state.continuity.interpretation, "listening");
    assert.equal(state.continuity.plt1, false);
    assert.equal(state.continuity.mat3, false);
    assert.equal(state.continuity.invariants.k3Integrability, true);
  });

  it("detects SA when governance behavior present", () => {
    const sa = withEventTags({
      id: "E_GOV",
      actor: "Alex",
      timestamp: "2026-06-23T23:00:00Z",
      accumulationType: "A3",
      targetsLayer: "Governance",
      fromExposure: true,
      buildsOn: [],
      governanceBehavior: "validate",
    });
    assert.equal(sa.origin, "SA");
  });

  it("CE-2 A(t) weights PLA, LA, SA strata", () => {
    const origins = {
      E1: "PLA" as const,
      E2: "LA" as const,
      E3: "LA" as const,
      E4: "SA" as const,
    };
    const saEvent = withEventTags({
      id: "E4",
      actor: "Alex",
      timestamp: "2026-06-23T23:00:00Z",
      accumulationType: "A3",
      targetsLayer: "Governance",
      fromExposure: true,
      buildsOn: [],
      governanceBehavior: "compress",
    });
    const events: JPSSContributionEvent[] = [
      { ...jonPla, id: "E1" },
      { ...sueLa, id: "E2" },
      { ...sueLa, id: "E3", actor: "Bradley" },
      saEvent,
    ];
    const metrics = computeContinuityMetrics(events, null, origins);
    assert.equal(metrics.accumulation.strata.pla, 1);
    assert.equal(metrics.accumulation.strata.la, 2);
    assert.equal(metrics.accumulation.strata.sa, 1);
    assert.equal(metrics.accumulation.value, 0.35 + 0.45 * 2 + 0.2);
  });
});
