import assert from "node:assert/strict";
import test from "node:test";
import { computeIdentityCycleDiff, deriveIdentityUserSignalsFromMessages } from "../server/identity-cycle";
import type { IdentitySnapshot } from "../server/identity-memory";
import type { Message } from "@shared/schema";

function buildSnapshot(): IdentitySnapshot {
  return {
    core: {
      schemaVersion: "identity-core.v1",
      version: 3,
      dominant_traits: {
        concise: 0.62,
        analytical: 0.74,
        symbolic: 0.38,
        challenging: 0.54,
        experimental: 0.42,
      },
      current_mode: "balanced",
      novelty_bias: 0.34,
      risk_tolerance: 0.46,
      self_stability: 0.76,
      last_updated_cycle: 10,
      updated_at: 1_700_000_000_000,
    },
    traits: {
      schemaVersion: "identity-traits.v1",
      emergent_patterns: [
        { name: "governance-defender", activation_frequency: 0.7, last_updated_cycle: 10 },
        { name: "wild-experimenter", activation_frequency: 0.35, last_updated_cycle: 10 },
      ],
    },
    impulses: {
      schemaVersion: "identity-impulses.v1",
      impulses: [
        {
          type: "refactor-suggestion",
          intensity: 0.3,
          cooldown: 0,
          base_cooldown: 3,
          last_updated_cycle: 10,
        },
        {
          type: "novel-structure-proposal",
          intensity: 0.24,
          cooldown: 0,
          base_cooldown: 5,
          last_updated_cycle: 10,
        },
        {
          type: "observability-expansion",
          intensity: 0.34,
          cooldown: 0,
          base_cooldown: 4,
          last_updated_cycle: 10,
        },
      ],
    },
  };
}

function msg(id: string, content: string, createdAt: number): Message {
  return {
    id,
    chatId: "chat-1",
    role: "user",
    content,
    createdAt,
  };
}

test("deriveIdentityUserSignalsFromMessages reads wild vs stability pressure deterministically", () => {
  const messages: Message[] = [
    msg("1", "I want wild evolution and more surprise.", 10),
    msg("2", "Keep it stable and deterministic please.", 9),
    msg("3", "This drift feels off.", 8),
    msg("4", "Good alignment now.", 7),
  ];
  const signals = deriveIdentityUserSignalsFromMessages(messages, "wild experimental push");
  assert.ok(signals.wildDemand > 0);
  assert.ok(signals.stabilityDemand > 0);
  assert.ok(signals.frustrationSignal > 0);
  assert.ok(signals.positiveSignal > 0);
  assert.ok(signals.explicitSignalBias > 0);
});

test("computeIdentityCycleDiff is deterministic for fixed inputs", () => {
  const input = {
    snapshot: buildSnapshot(),
    rotation: {
      totalRuns: 12,
      changeRate: 0.14,
      representativeChurnRate: 0.11,
      entropyVariance: 0.18,
      entropyTop1Share: 0.31,
    },
    shadow: {
      totalRuns: 12,
      disagreementMean: 0.21,
      disagreementRate: 0.28,
    },
    userSignals: {
      sampleSize: 12,
      wildDemand: 0.44,
      stabilityDemand: 0.2,
      frustrationSignal: 0.11,
      positiveSignal: 0.07,
      explicitSignalBias: 0.25,
      confidence: 0.72,
    },
    trigger: "identity-cycle:test",
    principalId: "anon:test",
    dryRun: true,
    now: 1_700_000_100_000,
  } as const;

  const first = computeIdentityCycleDiff(input);
  const second = computeIdentityCycleDiff(input);
  assert.deepEqual(first, second);
});

test("computeIdentityCycleDiff keeps bounded deltas", () => {
  const diff = computeIdentityCycleDiff({
    snapshot: buildSnapshot(),
    rotation: {
      totalRuns: 20,
      changeRate: 0.6,
      representativeChurnRate: 0.7,
      entropyVariance: 0.5,
      entropyTop1Share: 0.8,
    },
    shadow: {
      totalRuns: 20,
      disagreementMean: 0.5,
      disagreementRate: 0.7,
    },
    userSignals: {
      sampleSize: 20,
      wildDemand: 0.8,
      stabilityDemand: 0.1,
      frustrationSignal: 0.2,
      positiveSignal: 0.1,
      explicitSignalBias: 0.4,
      confidence: 1,
    },
    trigger: "identity-cycle:bounded",
    dryRun: true,
    now: 1_700_000_200_000,
  });

  for (const delta of Object.values(diff.deltas.core)) {
    assert.ok(Math.abs(delta.delta) <= 0.05 + 1e-9);
  }
  for (const delta of Object.values(diff.deltas.traits)) {
    assert.ok(Math.abs(delta.delta) <= 0.05 + 1e-9);
  }
  for (const delta of Object.values(diff.deltas.impulses)) {
    assert.ok(Math.abs(delta.delta) <= 0.06 + 1e-9);
  }
});

