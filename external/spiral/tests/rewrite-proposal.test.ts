import assert from "node:assert/strict";
import test from "node:test";
import type { Message } from "../shared/schema";
import { buildRewriteProposalDraft } from "../server/proposals/proposal-generator";
import { isProposalApplyableDiff } from "../shared/proposal-diff";

function message(overrides: Partial<Message>): Message {
  return {
    id: overrides.id || `m-${Math.random().toString(36).slice(2)}`,
    chatId: overrides.chatId || "chat-1",
    role: overrides.role || "user",
    content: overrides.content || "",
    createdAt: overrides.createdAt ?? Date.now(),
    ...(overrides.trace ? { trace: overrides.trace } : {}),
  };
}

test("proposal draft prioritizes sealed/silent assistant turns", () => {
  const draft = buildRewriteProposalDraft({
    principalId: "anon:test",
    chatId: "chat-1",
    messages: [
      message({ role: "user", content: "Which edge whispers?" }),
      message({ role: "assistant", content: "..." }),
    ],
  });

  assert.equal(draft.status, "pending");
  assert.equal(draft.observation.assistantSilenceTurns, 1);
  assert.equal(draft.proposedChange.kind, "prompt-fragment");
  assert.equal(draft.proposedChange.target, "server/veil-channel.mirror.ts");
  assert.equal(draft.governanceCheck?.requiresHumanPromotion, true);
  assert.equal(draft.governanceCheck?.applyableDiff, true);
});

test("proposal draft proposes UX copy refinement for repeated user turns", () => {
  const draft = buildRewriteProposalDraft({
    principalId: "anon:test",
    chatId: "chat-1",
    messages: [
      message({ role: "user", content: "Repeat me" }),
      message({ role: "assistant", content: "Acknowledged." }),
      message({ role: "user", content: "Repeat me" }),
    ],
  });

  assert.equal(draft.observation.repeatedUserTurns, 1);
  assert.equal(draft.proposedChange.kind, "ux-copy");
  assert.equal(draft.proposedChange.target, "client/src/components/chat-window.tsx");
  assert.equal(draft.governanceCheck?.commentOnlyDiff, false);
});

test("proposal draft fallback remains concrete/applyable for steady flow", () => {
  const draft = buildRewriteProposalDraft({
    principalId: "anon:test",
    chatId: "chat-1",
    messages: [
      message({ role: "user", content: "steady inquiry" }),
      message({ role: "assistant", content: "steady response" }),
    ],
  });

  assert.equal(isProposalApplyableDiff(draft.proposedChange.diffPreview), true);
  assert.equal(draft.governanceCheck?.requiresHumanPromotion, true);
  assert.ok((draft.governanceCheck?.notes.length || 0) >= 3);
});
