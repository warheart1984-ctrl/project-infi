import assert from "node:assert/strict";
import test from "node:test";
import { randomUUID } from "crypto";
import { mkdtemp, readFile, rm } from "fs/promises";
import { tmpdir } from "os";
import path from "path";
import type { RewriteProposal, RewriteProposalExecution } from "../shared/schema";
import { runRewriteProposalExecution } from "../server/proposals/proposal-executor";
import {
  recordRewriteProposalExecution,
  saveRewriteProposal,
  updateRewriteProposalStatus,
} from "../server/proposals/proposal-store";

async function withTempProposalRoot<T>(run: () => Promise<T>): Promise<T> {
  const previous = process.env.SPIRAL_PROPOSAL_ROOT;
  const dir = await mkdtemp(path.join(tmpdir(), "spiral-proposal-exec-"));
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

function buildExecution(overrides: Partial<RewriteProposalExecution> = {}): RewriteProposalExecution {
  return {
    runId: `run-${Math.random().toString(36).slice(2)}`,
    status: "succeeded",
    engine: "codex-oauth-stub",
    executedAt: Date.now(),
    executedBy: "anon:test",
    summary: "execution summary",
    ...overrides,
  };
}

function buildPendingProposal(): RewriteProposal {
  return {
    id: randomUUID(),
    principalId: "anon:test",
    chatId: "chat-exec",
    chatTitle: "Execution test chat",
    status: "pending",
    createdAt: Date.now(),
    summary: "proposal summary",
    observation: {
      totalMessages: 2,
      assistantSilenceTurns: 1,
      repeatedUserTurns: 0,
      longAssistantTurns: 0,
    },
    proposedChange: {
      kind: "prompt-fragment",
      target: "server/veil-channel.mirror.ts",
      rationale: "rationale",
      diffPreview:
        "--- a/server/veil-channel.mirror.ts\n+++ b/server/veil-channel.mirror.ts\n@@\n- old\n+ new",
    },
  };
}

function resolveArtifactPath(artifactPath: string): string {
  const normalized = artifactPath.replace(/\//g, path.sep);
  return path.isAbsolute(normalized) ? normalized : path.join(process.cwd(), normalized);
}

test("execution recording only works for accepted proposals", async () => {
  await withTempProposalRoot(async () => {
    const saved = await saveRewriteProposal(buildPendingProposal());

    const blocked = await recordRewriteProposalExecution({
      principalId: "anon:test",
      proposalId: saved.id,
      execution: buildExecution(),
    });
    assert.equal(blocked, null);

    const accepted = await updateRewriteProposalStatus({
      principalId: "anon:test",
      proposalId: saved.id,
      nextStatus: "accepted",
      decidedBy: "anon:test",
    });
    assert.ok(accepted);

    const recorded = await recordRewriteProposalExecution({
      principalId: "anon:test",
      proposalId: saved.id,
      execution: buildExecution(),
    });
    assert.ok(recorded);
    assert.equal(recorded.status, "accepted");
    assert.equal(recorded.execution?.engine, "codex-oauth-stub");
    assert.equal(recorded.execution?.status, "succeeded");
    assert.equal(recorded.executionRuns?.length, 1);

    const second = await recordRewriteProposalExecution({
      principalId: "anon:test",
      proposalId: saved.id,
      execution: buildExecution({ executedAt: Date.now() + 1 }),
    });
    assert.ok(second);
    assert.equal(second.executionRuns?.length, 2);
    assert.equal(second.execution?.runId, second.executionRuns?.[0]?.runId);
  });
});

test("execution runner writes log and patch artifacts", async () => {
  await withTempProposalRoot(async () => {
    const previousExecutor = process.env.SPIRAL_CODEX_EXECUTOR;
    process.env.SPIRAL_CODEX_EXECUTOR = "stub";
    let result: RewriteProposalExecution;
    const proposal = {
      ...buildPendingProposal(),
      status: "accepted" as const,
    };
    try {
      result = await runRewriteProposalExecution({
        proposal,
        principalId: "anon:test",
      });
    } finally {
      if (previousExecutor === undefined) {
        delete process.env.SPIRAL_CODEX_EXECUTOR;
      } else {
        process.env.SPIRAL_CODEX_EXECUTOR = previousExecutor;
      }
    }

    assert.equal(result!.status, "succeeded");
    assert.ok(result!.runId);
    assert.ok(result!.logArtifactPath);
    assert.ok(result!.patchArtifactPath);

    const logPath = resolveArtifactPath(result!.logArtifactPath || "");
    const patchPath = resolveArtifactPath(result!.patchArtifactPath || "");
    const [logContent, patchContent] = await Promise.all([
      readFile(logPath, "utf8"),
      readFile(patchPath, "utf8"),
    ]);

    assert.match(logContent, /No auto-apply path was used\./);
    assert.equal(patchContent, proposal.proposedChange.diffPreview);
  });
});

test("execution runner can synthesize fallback patch from proposal preview", async () => {
  await withTempProposalRoot(async () => {
    const previousExecutor = process.env.SPIRAL_CODEX_EXECUTOR;
    const previousTemplate = process.env.SPIRAL_CODEX_COMMAND_TEMPLATE;
    process.env.SPIRAL_CODEX_EXECUTOR = "codex-cli";
    process.env.SPIRAL_CODEX_COMMAND_TEMPLATE = "echo runner-ok";

    const proposal: RewriteProposal = {
      ...buildPendingProposal(),
      status: "accepted",
      proposedChange: {
        kind: "prompt-fragment",
        target: "server/spiral-process.ts",
        rationale: "rationale",
        diffPreview:
          "--- a/server/spiral-process.ts\n+++ b/server/spiral-process.ts\n@@ voice union\n-export type SpiralVoice = \"seer\" | \"daemon\" | \"child\";\n+export type SpiralVoice = \"seer\" | \"daemon\" | \"child\" | \"witness\";",
      },
    };

    let result: RewriteProposalExecution;
    try {
      result = await runRewriteProposalExecution({
        proposal,
        principalId: "anon:test",
      });
    } finally {
      if (previousExecutor === undefined) {
        delete process.env.SPIRAL_CODEX_EXECUTOR;
      } else {
        process.env.SPIRAL_CODEX_EXECUTOR = previousExecutor;
      }
      if (previousTemplate === undefined) {
        delete process.env.SPIRAL_CODEX_COMMAND_TEMPLATE;
      } else {
        process.env.SPIRAL_CODEX_COMMAND_TEMPLATE = previousTemplate;
      }
    }

    assert.equal(result!.status, "succeeded");
    assert.match(result!.summary, /deterministic patch fallback/i);
    assert.ok(result!.patchArtifactPath);

    const patchPath = resolveArtifactPath(result!.patchArtifactPath || "");
    const patchContent = await readFile(patchPath, "utf8");
    assert.match(patchContent, /server\/spiral-process\.ts/);
    assert.match(patchContent, /SpiralVoice/);
    assert.match(patchContent, /@@ -\d+/);
  });
});

test("execution fallback synthesis tolerates preview lines without trailing comma", async () => {
  await withTempProposalRoot(async () => {
    const previousExecutor = process.env.SPIRAL_CODEX_EXECUTOR;
    const previousTemplate = process.env.SPIRAL_CODEX_COMMAND_TEMPLATE;
    process.env.SPIRAL_CODEX_EXECUTOR = "codex-cli";
    process.env.SPIRAL_CODEX_COMMAND_TEMPLATE = "echo runner-ok";

    const proposal: RewriteProposal = {
      ...buildPendingProposal(),
      status: "accepted",
      proposedChange: {
        kind: "prompt-fragment",
        target: "server/spiral-process.ts",
        rationale: "rationale",
        diffPreview:
          "--- a/server/spiral-process.ts\n+++ b/server/spiral-process.ts\n@@ voice union\n-export type SpiralVoice = \"seer\" | \"daemon\" | \"child\"\n+export type SpiralVoice = \"seer\" | \"daemon\" | \"child\" | \"witness\"",
      },
    };

    let result: RewriteProposalExecution;
    try {
      result = await runRewriteProposalExecution({
        proposal,
        principalId: "anon:test",
      });
    } finally {
      if (previousExecutor === undefined) {
        delete process.env.SPIRAL_CODEX_EXECUTOR;
      } else {
        process.env.SPIRAL_CODEX_EXECUTOR = previousExecutor;
      }
      if (previousTemplate === undefined) {
        delete process.env.SPIRAL_CODEX_COMMAND_TEMPLATE;
      } else {
        process.env.SPIRAL_CODEX_COMMAND_TEMPLATE = previousTemplate;
      }
    }

    assert.equal(result!.status, "succeeded");
    const patchPath = resolveArtifactPath(result!.patchArtifactPath || "");
    const patchContent = await readFile(patchPath, "utf8");
    assert.match(patchContent, /\+\s*export type SpiralVoice = "seer" \| "daemon" \| "child" \| "witness";/);
  });
});

test("execution fallback synthesis supports add-only preview hunks", async () => {
  await withTempProposalRoot(async () => {
    const previousExecutor = process.env.SPIRAL_CODEX_EXECUTOR;
    const previousTemplate = process.env.SPIRAL_CODEX_COMMAND_TEMPLATE;
    process.env.SPIRAL_CODEX_EXECUTOR = "codex-cli";
    process.env.SPIRAL_CODEX_COMMAND_TEMPLATE = "echo runner-ok";

    const proposal: RewriteProposal = {
      ...buildPendingProposal(),
      status: "accepted",
      proposedChange: {
        kind: "guardrail",
        target: "server/spiral-process.ts",
        rationale: "rationale",
        diffPreview:
          "--- a/server/spiral-process.ts\n+++ b/server/spiral-process.ts\n@@ adaptation trace instrumentation\n+// Proposal-only test hook: synth add-only fallback line A.\n+// Proposal-only test hook: synth add-only fallback line B.",
      },
    };

    let result: RewriteProposalExecution;
    try {
      result = await runRewriteProposalExecution({
        proposal,
        principalId: "anon:test",
      });
    } finally {
      if (previousExecutor === undefined) {
        delete process.env.SPIRAL_CODEX_EXECUTOR;
      } else {
        process.env.SPIRAL_CODEX_EXECUTOR = previousExecutor;
      }
      if (previousTemplate === undefined) {
        delete process.env.SPIRAL_CODEX_COMMAND_TEMPLATE;
      } else {
        process.env.SPIRAL_CODEX_COMMAND_TEMPLATE = previousTemplate;
      }
    }

    assert.equal(result!.status, "succeeded");
    assert.match(result!.summary, /deterministic patch fallback/i);
    const patchPath = resolveArtifactPath(result!.patchArtifactPath || "");
    const patchContent = await readFile(patchPath, "utf8");
    assert.match(patchContent, /server\/spiral-process\.ts/);
    assert.match(
      patchContent,
      /\+\/\/ Proposal-only test hook: synth add-only fallback line A\./,
    );
    assert.match(
      patchContent,
      /\+\/\/ Proposal-only test hook: synth add-only fallback line B\./,
    );
  });
});

test("execution runner prefers a valid unified diff emitted in runner output", async () => {
  await withTempProposalRoot(async () => {
    const previousExecutor = process.env.SPIRAL_CODEX_EXECUTOR;
    const previousTemplate = process.env.SPIRAL_CODEX_COMMAND_TEMPLATE;
    process.env.SPIRAL_CODEX_EXECUTOR = "codex-cli";
    process.env.SPIRAL_CODEX_COMMAND_TEMPLATE =
      'pwsh -NoProfile -Command "$lines = @(\'```diff\', \'diff --git a/server/spiral-process.ts b/server/spiral-process.ts\', \'--- a/server/spiral-process.ts\', \'+++ b/server/spiral-process.ts\', \'@@ -30,1 +30,2 @@\', \'+// Runner patch line A.\', \'+// Runner patch line B.\', \'```\'); $lines"';

    const proposal: RewriteProposal = {
      ...buildPendingProposal(),
      status: "accepted",
      proposedChange: {
        kind: "guardrail",
        target: "server/spiral-process.ts",
        rationale: "rationale",
        diffPreview:
          "--- a/server/spiral-process.ts\n+++ b/server/spiral-process.ts\n@@ adaptation trace instrumentation\n+// Preview fallback line A.\n+// Preview fallback line B.",
      },
    };

    let result: RewriteProposalExecution;
    try {
      result = await runRewriteProposalExecution({
        proposal,
        principalId: "anon:test",
      });
    } finally {
      if (previousExecutor === undefined) {
        delete process.env.SPIRAL_CODEX_EXECUTOR;
      } else {
        process.env.SPIRAL_CODEX_EXECUTOR = previousExecutor;
      }
      if (previousTemplate === undefined) {
        delete process.env.SPIRAL_CODEX_COMMAND_TEMPLATE;
      } else {
        process.env.SPIRAL_CODEX_COMMAND_TEMPLATE = previousTemplate;
      }
    }

    assert.equal(result!.status, "succeeded");
    assert.ok(result!.patchArtifactPath);

    const patchPath = resolveArtifactPath(result!.patchArtifactPath || "");
    const patchContent = await readFile(patchPath, "utf8");
    assert.match(patchContent, /Runner patch line A\./);
    assert.match(patchContent, /Runner patch line B\./);
    assert.doesNotMatch(patchContent, /Preview fallback line A\./);
  });
});
