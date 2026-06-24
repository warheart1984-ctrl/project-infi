import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  correctJudgmentToward,
  computeJudgmentDrift,
  emptyJudgmentCapability,
  evaluateJudgment,
  isJudgmentFailure,
  judgmentFromObserver,
  JPA1_PRINCIPLES,
} from "../src/index.js";
import type { ObserverProfile } from "../src/css2/types.js";

describe("judgment capability", () => {
  it("evaluates composite score and weaknesses", () => {
    const cap = {
      ...emptyJudgmentCapability(),
      perception: 0.8,
      interpretation: 0.7,
      valuation: 0.3,
      deliberation: 0.35,
      commitment: 0.6,
      reflection: 0.2,
    };
    const result = evaluateJudgment(cap);
    assert.ok(result.score > 0.4 && result.score < 0.6);
    assert.ok(result.weaknesses.includes("Weak valuation"));
    assert.ok(result.weaknesses.includes("Weak deliberation"));
    assert.ok(result.weaknesses.includes("Weak reflection"));
  });

  it("detects judgment failure per JPA-1.5", () => {
    const weak = emptyJudgmentCapability();
    assert.equal(isJudgmentFailure(weak), true);
    const strong = {
      perception: 0.7,
      interpretation: 0.7,
      valuation: 0.7,
      deliberation: 0.7,
      commitment: 0.7,
      reflection: 0.7,
    };
    assert.equal(isJudgmentFailure(strong), false);
  });

  it("computes drift between profiles", () => {
    const prev = { ...emptyJudgmentCapability(), commitment: 0.5 };
    const curr = { ...emptyJudgmentCapability(), commitment: 0.9 };
    const drift = computeJudgmentDrift(prev, curr);
    assert.ok(drift > 0 && drift < 1);
  });

  it("corrects toward reference", () => {
    const current = { ...emptyJudgmentCapability(), valuation: 0.2 };
    const reference = { ...emptyJudgmentCapability(), valuation: 0.8 };
    const corrected = correctJudgmentToward(current, reference, 0.5);
    assert.ok(corrected.valuation > 0.2 && corrected.valuation < 0.8);
  });

  it("maps observer profile to judgment capability", () => {
    const observer: ObserverProfile = {
      id: "obs-1",
      name: "Test Observer",
      stage: "observer",
      joinedAt: "2026-01-01T00:00:00.000Z",
      capabilities: {
        perception: 0.6,
        interpretation: 0.5,
        hypothesis: 0.4,
        judgment: 0.7,
        stewardship: 0.3,
      },
      driftScore: 0.1,
      flags: {},
    };
    const cap = judgmentFromObserver(observer);
    assert.equal(cap.perception, 0.6);
    assert.equal(cap.deliberation, 0.4);
    assert.equal(cap.commitment, 0.7);
    assert.equal(cap.reflection, 0.3);
    assert.equal(cap.valuation, 0.45);
  });

  it("exports JPA-1 constitutional principles", () => {
    assert.ok(JPA1_PRINCIPLES.JPA_1_1.includes("judgment"));
    assert.ok(JPA1_PRINCIPLES.JPA_1_5.includes("ultimate continuity failure"));
  });
});
