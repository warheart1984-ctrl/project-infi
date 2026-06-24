import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  assessCorrigibility,
  assessLegitimateJudgment,
  annotateCorrigibility,
  buildLegitimateJudgmentInput,
  applyJudgmentCurriculumModule,
  createCapabilityLedger,
  createJudgmentCycleLedger,
  updateCapabilityLedger,
  detectJudgmentDriftTriggers,
  recordJudgmentDriftEvent,
  recordJudgmentCycle,
  makeJudgmentDriftTrace,
  JPSS2_JUDGMENT_CURRICULUM,
  emptyJudgmentCapability,
} from "../src/index.js";
import type { ObserverProfile } from "../src/css2/types.js";

function sampleObserver(overrides: Partial<ObserverProfile> = {}): ObserverProfile {
  return {
    id: "obs-jd-1",
    name: "Test Observer",
    stage: "observer",
    joinedAt: "2026-01-01T00:00:00.000Z",
    capabilities: {
      perception: 0.5,
      interpretation: 0.5,
      hypothesis: 0.4,
      judgment: 0.4,
      stewardship: 0.3,
    },
    driftScore: 0.1,
    flags: {},
    ...overrides,
  };
}

describe("CRK-1.J legitimate judgment", () => {
  it("requires all constitutional requirements including corrigibility", () => {
    const full = assessLegitimateJudgment({
      observationIntegrity: true,
      evidenceTraceable: true,
      invariantCompliant: true,
      stewardshipAccountable: true,
      judgmentCapabilityPreserved: true,
      corrigibilitySound: true,
    });
    assert.equal(full.legitimate, true);
    assert.equal(full.failedRequirements.length, 0);

    const partial = assessLegitimateJudgment({
      observationIntegrity: true,
      evidenceTraceable: false,
      invariantCompliant: true,
      stewardshipAccountable: true,
      judgmentCapabilityPreserved: true,
    });
    assert.equal(partial.legitimate, false);
    assert.ok(partial.failedRequirements.includes("evidenceTraceability"));
  });
});

describe("JPSS-2.J judgment curriculum", () => {
  it("has six capability modules", () => {
    assert.equal(JPSS2_JUDGMENT_CURRICULUM.length, 6);
  });

  it("applies perception 201 to observer stage", () => {
    const observer = sampleObserver();
    const mod = JPSS2_JUDGMENT_CURRICULUM.find((m) => m.id === "perception_201")!;
    const updated = applyJudgmentCurriculumModule(observer, mod);
    assert.ok(updated.capabilities.perception > observer.capabilities.perception);
  });

  it("maintains capability ledger with drift", () => {
    let observer = sampleObserver();
    const ledger = createCapabilityLedger(observer, "2026-01-01T00:00:00.000Z");
    observer = applyJudgmentCurriculumModule(
      observer,
      JPSS2_JUDGMENT_CURRICULUM.find((m) => m.id === "perception_201")!,
    );
    const updated = updateCapabilityLedger(ledger, observer, {
      moduleId: "perception_201",
      timestamp: "2026-01-02T00:00:00.000Z",
    });
    assert.equal(updated.trainingHistory.length, 2);
    assert.ok(updated.scores.perception >= ledger.scores.perception);
  });
});

describe("RA-COS-1.JD judgment drift trace", () => {
  it("triggers on drift threshold", () => {
    const previous = {
      ...emptyJudgmentCapability(),
      perception: 0.9,
      interpretation: 0.9,
      valuation: 0.8,
      deliberation: 0.7,
      commitment: 0.6,
      reflection: 0.5,
    };
    const current = {
      ...emptyJudgmentCapability(),
      perception: 0.2,
      interpretation: 0.2,
      valuation: 0.3,
      deliberation: 0.2,
      commitment: 0.1,
      reflection: 0.2,
    };
    const reasons = detectJudgmentDriftTriggers({
      observerId: "obs-1",
      previous,
      current,
    });
    assert.ok(reasons.includes("drift_threshold_exceeded"));
    assert.ok(reasons.includes("valuation_sharp_drop"));
    assert.ok(reasons.includes("deliberation_sharp_drop"));
  });

  it("records event and produces trace", () => {
    const previous = { ...emptyJudgmentCapability(), commitment: 0.9 };
    const current = { ...emptyJudgmentCapability(), commitment: 0.2 };
    const event = recordJudgmentDriftEvent({
      observerId: "obs-1",
      previous,
      current,
      contributingEvidence: [{ type: "threshold_delta", id: "t-1" }],
      timestamp: "2026-06-19T00:00:00.000Z",
    });
    assert.ok(event);
    assert.ok(event!.driftScore > 0);
    const trace = makeJudgmentDriftTrace(event!);
    assert.equal(trace.type, "judgment_drift");
    assert.equal(trace.actorId, "obs-1");
  });

  it("returns null when no triggers fire", () => {
    const cap = {
      ...emptyJudgmentCapability(),
      perception: 0.5,
      interpretation: 0.5,
      reflection: 0.5,
    };
    const event = recordJudgmentDriftEvent({
      observerId: "obs-1",
      previous: cap,
      current: { ...cap, perception: 0.51 },
      config: { driftThreshold: 0.5, reflectionStagnationMaxDelta: 0.001 },
    });
    assert.equal(event, null);
  });
});

describe("governance integration", () => {
  it("builds legitimate judgment input from governance context", () => {
    const input = buildLegitimateJudgmentInput({
      crkAllowed: true,
      evidenceCount: 3,
      identityIntentPreserved: true,
    });
    assert.equal(input.invariantCompliant, true);
    assert.equal(input.evidenceTraceable, true);
    assert.equal(input.corrigibilitySound, true);
  });
});

function soundCycle() {
  return {
    id: "jc-1",
    observerId: "obs-1",
    timestamp: "2026-06-19T00:00:00.000Z",
    observation: { source: "sensor", reading: 42 },
    interpretation: { framing: "latency spike", alternatives: ["noise", "load"] },
    valuation: { priority: "safety", rationale: "user impact" },
    decision: { actorId: "steward-1", action: "tighten threshold" },
    context: {},
    outcome: { metrics: { p99_ms: 120 } },
    feedback: { signal: "still high" },
    reflection: { changes: ["raise bound by 10ms"] },
  };
}

describe("CRK-1.J.5 corrigibility", () => {
  it("classifies sound cycle when all six checks pass", () => {
    const result = assessCorrigibility(soundCycle());
    assert.equal(result.status, "sound");
    assert.equal(result.violations, 0);
  });

  it("classifies failed cycle when corrigibility blocked", () => {
    const result = assessCorrigibility({
      ...soundCycle(),
      observation: null,
      interpretation: {},
      valuation: null,
      decision: {},
      outcome: {},
      reflection: {},
    });
    assert.equal(result.status, "failed");
    assert.ok(result.violations > 2);
  });

  it("annotates cycle with corrigibilityStatus", () => {
    const annotated = annotateCorrigibility(soundCycle());
    assert.equal(annotated.corrigibilityStatus, "sound");
  });

  it("blocks legitimacy when corrigibility fails", () => {
    const input = buildLegitimateJudgmentInput({
      crkAllowed: true,
      evidenceCount: 2,
      judgmentCycle: {
        ...soundCycle(),
        observation: null,
        interpretation: {},
        valuation: null,
        decision: {},
        outcome: {},
        reflection: {},
      },
    });
    const result = assessLegitimateJudgment(input);
    assert.equal(result.legitimate, false);
    assert.ok(result.failedRequirements.includes("corrigibility"));
  });

  it("records cycle in ledger with lineage rollup", () => {
    let ledger = createJudgmentCycleLedger("obs-1");
    ledger = recordJudgmentCycle(ledger, soundCycle());
    assert.equal(ledger.cycles.length, 1);
    assert.equal(ledger.lineageCorrigibility, "sound");
    assert.equal(ledger.cycles[0]!.cycle.corrigibilityStatus, "sound");
  });
});
