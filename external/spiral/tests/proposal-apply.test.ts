import assert from "node:assert/strict";
import test from "node:test";
import { randomUUID } from "crypto";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "fs/promises";
import { tmpdir } from "os";
import path from "path";
import type { RewriteProposal } from "../shared/schema";
import {
  applyRewriteProposalPatch,
  ProposalApplyError,
} from "../server/proposals/proposal-applier";

interface CommandResult {
  exitCode: number;
  stdout: string;
  stderr: string;
}

async function runCommand(command: string, args: string[], cwd: string): Promise<CommandResult> {
  const { spawn } = await import("child_process");
  return await new Promise((resolve) => {
    const child = spawn(command, args, {
      cwd,
      env: process.env,
      windowsHide: true,
    });
    let stdout = "";
    let stderr = "";
    child.stdout?.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr?.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", (error) => {
      stderr += `${error.name}: ${error.message}\n`;
      resolve({ exitCode: -1, stdout, stderr });
    });
    child.on("close", (code) => {
      resolve({ exitCode: typeof code === "number" ? code : -1, stdout, stderr });
    });
  });
}

async function withTempRepo<T>(run: (repoRoot: string) => Promise<T>): Promise<T> {
  const dir = await mkdtemp(path.join(tmpdir(), "spiral-proposal-apply-"));
  try {
    const init = await runCommand("git", ["init"], dir);
    assert.equal(init.exitCode, 0, init.stderr || init.stdout);
    return await run(dir);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

function buildAcceptedProposal(patchArtifactPath: string): RewriteProposal {
  return {
    id: randomUUID(),
    principalId: "anon:test",
    chatId: "chat-apply",
    chatTitle: "Apply test chat",
    status: "accepted",
    createdAt: Date.now(),
    summary: "Apply proposal patch",
    observation: {
      totalMessages: 2,
      assistantSilenceTurns: 0,
      repeatedUserTurns: 1,
      longAssistantTurns: 0,
    },
    proposedChange: {
      kind: "prompt-fragment",
      target: "target.txt",
      rationale: "test rationale",
      diffPreview: "--- a/target.txt\n+++ b/target.txt\n@@ -1 +1 @@\n-old\n+new",
    },
    executionRuns: [
      {
        runId: "run-1",
        status: "succeeded",
        engine: "codex-oauth-stub",
        executedAt: Date.now(),
        executedBy: "anon:test",
        summary: "ok",
        patchArtifactPath,
      },
    ],
  };
}

test("applyRewriteProposalPatch applies a successful execution patch", async () => {
  await withTempRepo(async (repoRoot) => {
    const filePath = path.join(repoRoot, "target.txt");
    const patchArtifactPath = "proposals/executions/p1/run-1/generated.patch";
    const patchPath = path.join(repoRoot, patchArtifactPath.replace(/\//g, path.sep));
    await mkdir(path.dirname(patchPath), { recursive: true });
    await writeFile(filePath, "old\n", "utf8");
    await writeFile(
      patchPath,
      ["--- a/target.txt", "+++ b/target.txt", "@@ -1 +1 @@", "-old", "+new", ""].join("\n"),
      "utf8",
    );

    const proposal = buildAcceptedProposal(patchArtifactPath);
    const applied = await applyRewriteProposalPatch({
      proposal,
      principalId: "anon:test",
      repoRoot,
    });

    const updated = await readFile(filePath, "utf8");
    assert.equal(updated.replace(/\r\n/g, "\n"), "new\n");
    assert.equal(applied.appliedBy, "anon:test");
    assert.equal(applied.runId, "run-1");
    assert.equal(applied.patchArtifactPath, patchArtifactPath);
  });
});

test("applyRewriteProposalPatch rejects proposals without successful execution runs", async () => {
  await withTempRepo(async (repoRoot) => {
    const proposal = buildAcceptedProposal("proposals/executions/p1/run-1/generated.patch");
    proposal.executionRuns = [
      {
        runId: "run-failed",
        status: "failed",
        engine: "codex-cli",
        executedAt: Date.now(),
        executedBy: "anon:test",
        summary: "failed",
        patchArtifactPath: "proposals/executions/p1/run-1/generated.patch",
      },
    ];

    await assert.rejects(
      () =>
        applyRewriteProposalPatch({
          proposal,
          principalId: "anon:test",
          repoRoot,
        }),
      (error: unknown) =>
        error instanceof ProposalApplyError &&
        error.statusCode === 409 &&
        /successful execution run/i.test(error.message),
    );
  });
});

test("applyRewriteProposalPatch rejects symbolic/non-unified patch artifacts", async () => {
  await withTempRepo(async (repoRoot) => {
    const filePath = path.join(repoRoot, "target.txt");
    const patchArtifactPath = "proposals/executions/p1/run-symbolic/generated.patch";
    const patchPath = path.join(repoRoot, patchArtifactPath.replace(/\//g, path.sep));
    await mkdir(path.dirname(patchPath), { recursive: true });
    await writeFile(filePath, "old\n", "utf8");
    await writeFile(
      patchPath,
      [
        "--- a/target.txt",
        "+++ b/target.txt",
        "@@ symbolic marker",
        "-old",
        "+new",
        "",
      ].join("\n"),
      "utf8",
    );

    const proposal = buildAcceptedProposal(patchArtifactPath);
    await assert.rejects(
      () =>
        applyRewriteProposalPatch({
          proposal,
          principalId: "anon:test",
          repoRoot,
        }),
      (error: unknown) =>
        error instanceof ProposalApplyError &&
        error.statusCode === 409 &&
        /no applicable git patch/i.test(error.message),
    );
  });
});

test("applyRewriteProposalPatch rejects advisory/comment-only proposals", async () => {
  await withTempRepo(async (repoRoot) => {
    const patchArtifactPath = "proposals/executions/p1/run-1/generated.patch";
    const proposal = buildAcceptedProposal(patchArtifactPath);
    proposal.proposedChange.diffPreview = [
      "--- a/target.txt",
      "+++ b/target.txt",
      "@@ comment-only",
      "+ // advisory note",
      "+ // no concrete code change",
      "",
    ].join("\n");

    await assert.rejects(
      () =>
        applyRewriteProposalPatch({
          proposal,
          principalId: "anon:test",
          repoRoot,
        }),
      (error: unknown) =>
        error instanceof ProposalApplyError &&
        error.statusCode === 409 &&
        /advisory-only/i.test(error.message),
    );
  });
});
