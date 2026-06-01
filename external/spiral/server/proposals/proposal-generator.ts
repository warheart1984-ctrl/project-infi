import { randomUUID } from "crypto";
import type { Message, RewriteProposal } from "@shared/schema";
import { isProposalApplyableDiff } from "@shared/proposal-diff";
import { evaluateRewriteProposalGovernance } from "./proposal-governance";

interface BuildRewriteProposalInput {
  principalId: string;
  chatId: string;
  chatTitle?: string;
  messages: Message[];
  signal?: string;
}

function normalizeText(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

function countAssistantSilenceTurns(messages: Message[]): number {
  return messages.filter((message) => {
    if (message.role !== "assistant") return false;
    const content = normalizeText(message.content || "");
    return content.length === 0 || content === "...";
  }).length;
}

function countRepeatedUserTurns(messages: Message[]): number {
  let repeats = 0;
  let previous = "";
  let hasPrevious = false;

  for (const message of messages) {
    if (message.role !== "user") continue;
    const content = normalizeText(message.content || "");
    if (!content) continue;
    if (hasPrevious && content === previous) {
      repeats += 1;
    }
    previous = content;
    hasPrevious = true;
  }

  return repeats;
}

function countLongAssistantTurns(messages: Message[]): number {
  return messages.filter((message) => message.role === "assistant" && message.content.trim().length >= 1200).length;
}

function clampSummary(value: string): string {
  const trimmed = value.trim();
  if (trimmed.length <= 500) return trimmed;
  return `${trimmed.slice(0, 497)}...`;
}

export function buildRewriteProposalDraft(input: BuildRewriteProposalInput): RewriteProposal {
  const assistantSilenceTurns = countAssistantSilenceTurns(input.messages);
  const repeatedUserTurns = countRepeatedUserTurns(input.messages);
  const longAssistantTurns = countLongAssistantTurns(input.messages);
  const totalMessages = input.messages.length;

  const observation = {
    totalMessages,
    assistantSilenceTurns,
    repeatedUserTurns,
    longAssistantTurns,
  };

  let summary = "Observed steady flow. Propose a small guardrail refinement for clarity continuity.";
  let proposedChange: RewriteProposal["proposedChange"] = {
    kind: "ux-copy",
    target: "client/src/components/chat-window.tsx",
    rationale:
      "No high-friction signal was detected, so default to a low-risk UI clarity tweak that still results in a concrete, reviewable code change.",
    diffPreview: [
      "--- a/client/src/components/chat-window.tsx",
      "+++ b/client/src/components/chat-window.tsx",
      "@@ recovery hint near stillness banner",
      '+ <p className="text-xs text-muted-foreground">Flow may remain quiet between pulses.</p>',
    ].join("\n"),
  };

  if (assistantSilenceTurns > 0) {
    summary = `Observed ${assistantSilenceTurns} sealed/silent assistant turns. Propose silent gate fallback enforcement.`;
    proposedChange = {
      kind: "prompt-fragment",
      target: "server/veil-channel.mirror.ts",
      rationale:
        "Sealed gate behavior should remain binary and non-expressive. Empty fallback output preserves enforcement without conversational drift.",
      diffPreview: [
        "--- a/server/veil-channel.mirror.ts",
        "+++ b/server/veil-channel.mirror.ts",
        "@@ sealed gate fallback",
        '-       reply: "..."',
        '+       reply: ""',
      ].join("\n"),
    };
  } else if (repeatedUserTurns > 0) {
    summary = `Observed ${repeatedUserTurns} repeated user turns. Propose clearer in-UI recovery guidance when repetition is detected.`;
    proposedChange = {
      kind: "ux-copy",
      target: "client/src/components/chat-window.tsx",
      rationale:
        "When users repeat the same line, the current transcript can feel stuck. A compact hint can suggest the next viable move without changing any gate behavior.",
      diffPreview: [
        "--- a/client/src/components/chat-window.tsx",
        "+++ b/client/src/components/chat-window.tsx",
        "@@ recovery hint near stillness banner",
        '+ <p className="text-xs text-muted-foreground">Repetition detected. Field may remain quiet.</p>',
      ].join("\n"),
    };
  } else if (longAssistantTurns > 0) {
    summary = `Observed ${longAssistantTurns} long assistant turns. Propose tighter voice-shift guidance for compact output.`;
    proposedChange = {
      kind: "voice-shift",
      target: "server/veil-channel.mirror.ts",
      rationale:
        "Long responses can dilute signal density. A compactness instruction in ritual shaping keeps flow legible while preserving tone.",
      diffPreview: [
        "--- a/server/veil-channel.mirror.ts",
        "+++ b/server/veil-channel.mirror.ts",
        "@@ ritual response shaping",
        '+     "Prefer short, high-signal blocks unless detail is explicitly requested.",',
      ].join("\n"),
    };
  }

  if (!isProposalApplyableDiff(proposedChange.diffPreview)) {
    summary = "Observed advisory-only proposal content. Reframed as concrete UX copy refinement for safe review/apply.";
    proposedChange = {
      kind: "ux-copy",
      target: "client/src/components/chat-window.tsx",
      rationale:
        "Comment-only and non-concrete diffs are filtered out. This fallback keeps proposal intent practical, visible, and applyable.",
      diffPreview: [
        "--- a/client/src/components/chat-window.tsx",
        "+++ b/client/src/components/chat-window.tsx",
        "@@ recovery hint near stillness banner",
        '+ <p className="text-xs text-muted-foreground">Repetition detected. Field may remain quiet.</p>',
      ].join("\n"),
    };
  }

  return {
    id: randomUUID(),
    principalId: input.principalId,
    chatId: input.chatId,
    ...(input.chatTitle ? { chatTitle: input.chatTitle.slice(0, 200) } : {}),
    status: "pending",
    createdAt: Date.now(),
    ...(input.signal ? { signal: input.signal.slice(0, 280) } : {}),
    summary: clampSummary(summary),
    observation,
    proposedChange,
    governanceCheck: evaluateRewriteProposalGovernance(proposedChange),
  };
}
