import assert from "node:assert/strict";
import test from "node:test";
import { randomUUID } from "crypto";
import { mkdtemp, readFile, readdir, rm } from "fs/promises";
import { tmpdir } from "os";
import path from "path";
import type { RewriteProposal } from "../shared/schema";
import {
  archiveRewriteProposalsByIds,
  listRewriteProposals,
  recordRewriteProposalApply,
  saveRewriteProposal,
  updateRewriteProposalStatus,
} from "../server/proposals/proposal-store";

async function withTempProposalRoot<T>(run: () => Promise<T>): Promise<T> {
  const previous = process.env.SPIRAL_PROPOSAL_ROOT;
  const dir = await mkdtemp(path.join(tmpdir(), "spiral-proposals-"));
  process.env.SPIRAL_PROPOSAL_ROOT = dir;
  try {
    return await run();
  } finally {
    if (previous === undefined) {
      delete process.env.SPIRAL_PROPOSAL_ROOT;
    } else {
      process.env.SPIRAL_PROPOSAL_ROOT = previous;
    }
    await rm(dir, { recursive: true, force: true });
  }
}

test("accepting a proposal updates status and decision metadata", async () => {
  await withTempProposalRoot(async () => {
    const pending: RewriteProposal = {
      id: randomUUID(),
      principalId: "anon:test",
      chatId: "chat-1",
      chatTitle: "Test chat",
      status: "pending",
      createdAt: Date.now(),
      summary: "proposal summary",
      observation: {
        totalMessages: 3,
        assistantSilenceTurns: 1,
        repeatedUserTurns: 0,
        longAssistantTurns: 0,
      },
      proposedChange: {
        kind: "prompt-fragment",
        target: "server/veil-channel.mirror.ts",
        rationale: "rationale",
        diffPreview: "--- a\n+++ b",
      },
    };

    const saved = await saveRewriteProposal(pending);
    const accepted = await updateRewriteProposalStatus({
      principalId: "anon:test",
      proposalId: saved.id,
      nextStatus: "accepted",
      decidedBy: "anon:test",
      reason: "Looks good",
    });

    assert.ok(accepted);
    assert.equal(accepted.status, "accepted");
    assert.equal(accepted.decidedBy, "anon:test");
    assert.equal(accepted.decisionReason, "Looks good");
    assert.ok(typeof accepted.decidedAt === "number" && accepted.decidedAt > 0);
    assert.ok(accepted.artifactPath?.includes("/accepted/"));
    assert.equal(accepted.governanceCheck?.requiresHumanPromotion, true);
  });
});

test("proposal decision is principal-scoped", async () => {
  await withTempProposalRoot(async () => {
    const saved = await saveRewriteProposal({
      id: randomUUID(),
      principalId: "anon:owner",
      chatId: "chat-2",
      status: "pending",
      createdAt: Date.now(),
      summary: "proposal summary",
      observation: {
        totalMessages: 4,
        assistantSilenceTurns: 0,
        repeatedUserTurns: 1,
        longAssistantTurns: 0,
      },
      proposedChange: {
        kind: "ux-copy",
        target: "client/src/components/chat-window.tsx",
        rationale: "rationale",
        diffPreview: "--- a\n+++ b",
      },
    });

    const rejected = await updateRewriteProposalStatus({
      principalId: "anon:other",
      proposalId: saved.id,
      nextStatus: "rejected",
      decidedBy: "anon:other",
      reason: "Not owner",
    });

    assert.equal(rejected, null);
  });
});

test("recording proposal apply metadata is accepted-and-principal scoped", async () => {
  await withTempProposalRoot(async () => {
    const previousJournalPath = process.env.SPIRAL_PROPOSAL_APPLY_JOURNAL_PATH;
    const journalPath = path.join(process.env.SPIRAL_PROPOSAL_ROOT || "", "apply-journal.md");
    process.env.SPIRAL_PROPOSAL_APPLY_JOURNAL_PATH = journalPath;
    const saved = await saveRewriteProposal({
      id: randomUUID(),
      principalId: "anon:owner",
      chatId: "chat-apply",
      status: "pending",
      createdAt: Date.now(),
      summary: "proposal summary",
      observation: {
        totalMessages: 2,
        assistantSilenceTurns: 0,
        repeatedUserTurns: 1,
        longAssistantTurns: 0,
      },
      proposedChange: {
        kind: "prompt-fragment",
        target: "server/veil-channel.mirror.ts",
        rationale: "rationale",
        diffPreview: "--- a\n+++ b",
      },
    });

    try {
      const blockedPending = await recordRewriteProposalApply({
        principalId: "anon:owner",
        proposalId: saved.id,
        apply: {
          runId: "run-1",
          appliedAt: Date.now(),
          appliedBy: "anon:owner",
          patchArtifactPath: "proposals/executions/x/generated.patch",
          summary: "applied",
        },
      });
      assert.equal(blockedPending, null);

      const accepted = await updateRewriteProposalStatus({
        principalId: "anon:owner",
        proposalId: saved.id,
        nextStatus: "accepted",
        decidedBy: "anon:owner",
      });
      assert.ok(accepted);

      const blockedPrincipal = await recordRewriteProposalApply({
        principalId: "anon:other",
        proposalId: saved.id,
        apply: {
          runId: "run-1",
          appliedAt: Date.now(),
          appliedBy: "anon:other",
          patchArtifactPath: "proposals/executions/x/generated.patch",
          summary: "applied",
        },
      });
      assert.equal(blockedPrincipal, null);

      const recorded = await recordRewriteProposalApply({
        principalId: "anon:owner",
        proposalId: saved.id,
        apply: {
          runId: "run-1",
          appliedAt: Date.now(),
          appliedBy: "anon:owner",
          patchArtifactPath: "proposals/executions/x/generated.patch",
          summary: "applied",
        },
      });
      assert.ok(recorded);
      assert.equal(recorded.apply?.appliedBy, "anon:owner");
      assert.equal(recorded.apply?.runId, "run-1");
      const journalContent = await readFile(journalPath, "utf8");
      assert.match(journalContent, /Proposal:/);
      assert.match(journalContent, /Target: server\/veil-channel\.mirror\.ts/);
      assert.match(journalContent, /Why: proposal summary/);
    } finally {
      if (previousJournalPath === undefined) {
        delete process.env.SPIRAL_PROPOSAL_APPLY_JOURNAL_PATH;
      } else {
        process.env.SPIRAL_PROPOSAL_APPLY_JOURNAL_PATH = previousJournalPath;
      }
    }
  });
});

test("archiving proposals moves them out of active list into proposals/archived", async () => {
  await withTempProposalRoot(async () => {
    const proposal = await saveRewriteProposal({
      id: randomUUID(),
      principalId: "anon:owner",
      chatId: "chat-archive",
      status: "pending",
      createdAt: Date.now(),
      summary: "archive me",
      observation: {
        totalMessages: 1,
        assistantSilenceTurns: 0,
        repeatedUserTurns: 0,
        longAssistantTurns: 0,
      },
      proposedChange: {
        kind: "ux-copy",
        target: "client/src/components/chat-window.tsx",
        rationale: "rationale",
        diffPreview: "--- a\n+++ b",
      },
    });

    const archived = await archiveRewriteProposalsByIds({
      principalId: "anon:owner",
      proposalIds: [proposal.id],
    });
    assert.equal(archived.length, 1);
    assert.match(archived[0].artifactPath || "", /proposals\/archived\//);

    const active = await listRewriteProposals({
      principalId: "anon:owner",
      limit: 20,
    });
    assert.equal(active.length, 0);

    const archivedDir = path.join(process.env.SPIRAL_PROPOSAL_ROOT || "", "archived");
    const archivedFiles = await readdir(archivedDir);
    assert.ok(archivedFiles.some((name) => name.includes(proposal.id)));
  });
});
