import assert from "node:assert/strict";
import test from "node:test";
import { parseEvolutionCommand, renderEvolutionStateSummary } from "../server/evolution-command";
import type { PrincipalEvolutionState } from "../server/evolution-state";

test("parseEvolutionCommand resolves status aliases", () => {
  assert.deepEqual(parseEvolutionCommand("/evolve"), { type: "status" });
  assert.deepEqual(parseEvolutionCommand("evolve status"), { type: "status" });
  assert.deepEqual(parseEvolutionCommand("/bg"), { type: "status" });
  assert.deepEqual(parseEvolutionCommand("/bg status"), { type: "status" });
});

test("parseEvolutionCommand resolves mode and control toggles", () => {
  assert.deepEqual(parseEvolutionCommand("/evolve on"), { type: "set-mode", mode: "wild" });
  assert.deepEqual(parseEvolutionCommand("/evolve off"), { type: "set-mode", mode: "still" });
  assert.deepEqual(parseEvolutionCommand("/bg on"), { type: "set-background", enabled: true });
  assert.deepEqual(parseEvolutionCommand("/bg off"), { type: "set-background", enabled: false });
  assert.deepEqual(parseEvolutionCommand("/evolve auto-apply on"), {
    type: "set-auto-apply",
    enabled: true,
  });
  assert.deepEqual(parseEvolutionCommand("/evolve apply off"), {
    type: "set-auto-apply",
    enabled: false,
  });
  assert.deepEqual(parseEvolutionCommand("/evolve seal on"), {
    type: "set-mutation-seal",
    enabled: true,
  });
  assert.deepEqual(parseEvolutionCommand("/evolve mutation-seal off"), {
    type: "set-mutation-seal",
    enabled: false,
  });
});

test("parseEvolutionCommand resolves cycle commands with optional signal", () => {
  assert.deepEqual(parseEvolutionCommand("/evolve cycle"), { type: "cycle" });
  assert.deepEqual(parseEvolutionCommand("/evolve cycle tighten drift checks"), {
    type: "cycle",
    signal: "tighten drift checks",
  });
});

test("parseEvolutionCommand ignores unrelated prompts", () => {
  assert.equal(parseEvolutionCommand("remember this"), undefined);
  assert.equal(parseEvolutionCommand("self evaluate"), undefined);
  assert.equal(parseEvolutionCommand("/evolve unknown"), undefined);
});

test("renderEvolutionStateSummary includes key runtime fields", () => {
  const state: PrincipalEvolutionState = {
    mode: "wild",
    backgroundPulseEnabled: true,
    autoApplyEnabled: false,
    mutationSealEnabled: true,
    updatedAt: 100,
    lastSeenChatId: "chat-1",
    lastCycleAt: 0,
    lastCycleStatus: "drafted",
    lastCycleSummary: "Draft created.",
    lastProposalId: "proposal-1",
    lastObservationAuditAt: 150,
    lastObservationAuditSummary: "Observation audit: gatesFailed=0 mimicryFindings=0",
  };
  const summary = renderEvolutionStateSummary(state, 200);
  assert.ok(summary.includes("Evolution mode: WILD"));
  assert.ok(summary.includes("Background pulse: ON"));
  assert.ok(summary.includes("Auto-apply: OFF"));
  assert.ok(summary.includes("Mutation seal: ON"));
  assert.ok(summary.includes("Last proposal: proposal-1"));
  assert.ok(summary.includes("Last observation audit: Observation audit: gatesFailed=0 mimicryFindings=0"));
});
