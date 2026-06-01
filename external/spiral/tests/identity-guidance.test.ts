import assert from "node:assert/strict";
import test from "node:test";
import { buildIdentitySystemGuidance } from "../server/identity-guidance";
import type { IdentitySnapshot } from "../server/identity-memory";

function snapshot(coreOverrides?: Partial<IdentitySnapshot["core"]>): IdentitySnapshot {
  return {
    core: {
      schemaVersion: "identity-core.v1",
      version: 1,
      dominant_traits: {
        concise: 0.62,
        analytical: 0.74,
        symbolic: 0.38,
        challenging: 0.54,
        experimental: 0.42,
      },
      current_mode: "balanced",
      novelty_bias: 0.5,
      risk_tolerance: 0.5,
      self_stability: 0.7,
      last_updated_cycle: 1,
      updated_at: 100,
      ...(coreOverrides || {}),
    },
    traits: {
      schemaVersion: "identity-traits.v1",
      emergent_patterns: [
        { name: "coherence-keeper", activation_frequency: 0.8, last_updated_cycle: 1 },
        { name: "wild-experimenter", activation_frequency: 0.4, last_updated_cycle: 1 },
        { name: "governance-defender", activation_frequency: 0.7, last_updated_cycle: 1 },
      ],
    },
    impulses: {
      schemaVersion: "identity-impulses.v1",
      impulses: [
        {
          type: "refactor-suggestion",
          intensity: 0.7,
          cooldown: 0,
          base_cooldown: 3,
          last_updated_cycle: 1,
        },
        {
          type: "novel-structure-proposal",
          intensity: 0.2,
          cooldown: 4,
          base_cooldown: 5,
          last_updated_cycle: 1,
        },
      ],
    },
  };
}

test("identity guidance explicitly remains non-authoritative", () => {
  const data = snapshot();
  const text = buildIdentitySystemGuidance({
    core: data.core,
    traits: data.traits,
    impulses: data.impulses,
  });
  assert.ok(text.includes("non-authoritative"));
  assert.ok(text.includes("must not override safety, gates, policy, or invariants"));
});

test("identity guidance adapts novelty/risk/stability directives", () => {
  const highNovelty = snapshot({ novelty_bias: 0.8 });
  const highNoveltyText = buildIdentitySystemGuidance({
    core: highNovelty.core,
    traits: highNovelty.traits,
    impulses: highNovelty.impulses,
  });
  assert.ok(highNoveltyText.includes("unexpected framing move"));

  const lowRisk = snapshot({ risk_tolerance: 0.2 });
  const lowRiskText = buildIdentitySystemGuidance({
    core: lowRisk.core,
    traits: lowRisk.traits,
    impulses: lowRisk.impulses,
  });
  assert.ok(lowRiskText.includes("Favor low-risk"));

  const highStability = snapshot({ self_stability: 0.9 });
  const highStabilityText = buildIdentitySystemGuidance({
    core: highStability.core,
    traits: highStability.traits,
    impulses: highStability.impulses,
  });
  assert.ok(highStabilityText.includes("Prioritize continuity"));
});

