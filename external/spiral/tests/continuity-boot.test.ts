import assert from "node:assert/strict";
import test from "node:test";
import { renderContinuityBootSummary } from "../server/continuity-boot";

test("renderContinuityBootSummary includes continuity state fields", () => {
  const summary = renderContinuityBootSummary({
    memoryMode: "sigil-bound",
    evolutionMode: "wild",
    mutationSealEnabled: true,
    lastCycleStatus: "executed",
    lastCycleSummary: "Autonomous apply remains sealed.",
    latestProposal: {
      id: "proposal-1",
      status: "accepted",
    },
    pendingProposalCount: 2,
    identityMode: "balanced",
    identityStability: 0.76,
  });

  assert.match(summary, /Memory mode: sigil-bound/);
  assert.match(summary, /Mutation seal: ON/);
  assert.match(summary, /Latest proposal: proposal-1 \(accepted\)/);
  assert.match(summary, /Pending proposals: 2/);
});
