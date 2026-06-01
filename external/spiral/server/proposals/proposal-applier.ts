import { spawn } from "child_process";
import { access, readFile } from "fs/promises";
import path from "path";
import type { RewriteProposal, RewriteProposalApply, RewriteProposalExecution } from "@shared/schema";
import { isProposalApplyableDiff } from "@shared/proposal-diff";

interface ApplyRewriteProposalPatchInput {
  proposal: RewriteProposal;
  principalId: string;
  runId?: string;
  repoRoot?: string;
}

interface ResolvedRunPatch {
  run: RewriteProposalExecution;
  patchAbsolutePath: string;
}

interface GitCommandResult {
  exitCode: number;
  stdout: string;
  stderr: string;
}

export class ProposalApplyError extends Error {
  statusCode: number;

  constructor(message: string, statusCode = 400) {
    super(message);
    this.name = "ProposalApplyError";
    this.statusCode = statusCode;
  }
}

function normalizePrincipal(value: string): string {
  return value.trim().slice(0, 200);
}

function getExecutionRuns(proposal: RewriteProposal): RewriteProposalExecution[] {
  const fromRuns = Array.isArray(proposal.executionRuns) ? proposal.executionRuns : [];
  const merged = proposal.execution ? [proposal.execution, ...fromRuns] : fromRuns;
  const map = new Map<string, RewriteProposalExecution>();
  for (const run of merged) {
    if (!run) continue;
    const fallbackRunId =
      typeof run.executedAt === "number"
        ? `legacy-${run.executedAt}-${run.engine}`
        : `legacy-${map.size + 1}`;
    const runId = (run.runId || fallbackRunId).trim();
    if (!runId || map.has(runId)) continue;
    map.set(runId, { ...run, runId });
  }
  return Array.from(map.values()).sort((a, b) => b.executedAt - a.executedAt);
}

function firstContentLine(value: string): string | undefined {
  const line = value
    .split(/\r?\n/)
    .map((candidate) => candidate.trim())
    .find(Boolean);
  if (!line) return undefined;
  return line.length > 220 ? `${line.slice(0, 217)}...` : line;
}

async function runGitCommand(args: string[], cwd: string): Promise<GitCommandResult> {
  const gitArgs = ["-c", `safe.directory=${cwd}`, ...args];
  return await new Promise((resolve) => {
    const child = spawn("git", gitArgs, {
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

function resolvePatchAbsolutePath(patchArtifactPath: string, repoRoot: string): string {
  const normalizedPath = patchArtifactPath.replace(/\//g, path.sep);
  const absolutePath = path.resolve(repoRoot, normalizedPath);
  const relativePath = path.relative(repoRoot, absolutePath);
  if (relativePath.startsWith("..") || path.isAbsolute(relativePath)) {
    throw new ProposalApplyError("Patch artifact path escapes repository root.", 400);
  }
  return absolutePath;
}

function resolveExecutionRun(
  proposal: RewriteProposal,
  requestedRunId?: string,
): RewriteProposalExecution {
  const runs = getExecutionRuns(proposal);
  if (runs.length === 0) {
    throw new ProposalApplyError(
      "No execution runs found. Execute the accepted proposal before applying.",
      409,
    );
  }

  const selected = requestedRunId
    ? runs.find((run) => (run.runId || "").trim() === requestedRunId.trim())
    : runs.find((run) => run.status === "succeeded" && Boolean(run.patchArtifactPath));
  if (!selected) {
    if (requestedRunId) {
      throw new ProposalApplyError(`Execution run "${requestedRunId}" was not found.`, 404);
    }
    throw new ProposalApplyError(
      "No successful execution run with a patch artifact is available to apply.",
      409,
    );
  }
  if (selected.status !== "succeeded") {
    throw new ProposalApplyError(
      "The selected execution run failed. Apply requires a successful execution run.",
      409,
    );
  }
  if (!selected.patchArtifactPath) {
    throw new ProposalApplyError("Selected execution run has no patch artifact.", 409);
  }
  return selected;
}

function looksLikeUnifiedDiff(patchText: string): boolean {
  if (!patchText.trim()) return false;
  if (/^diff --git /m.test(patchText)) return true;
  const hasHeader = /^---\s+\S+/m.test(patchText) && /^\+\+\+\s+\S+/m.test(patchText);
  const hasHunk = /^@@\s*-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s*@@/m.test(patchText);
  return hasHeader && hasHunk;
}

async function resolveApplicableRunPatch(
  proposal: RewriteProposal,
  repoRoot: string,
  requestedRunId?: string,
): Promise<ResolvedRunPatch> {
  const selected = resolveExecutionRun(proposal, requestedRunId);
  const preferredCandidates = requestedRunId
    ? [selected]
    : [
        selected,
        ...getExecutionRuns(proposal).filter(
          (run) =>
            (run.runId || "").trim() !== (selected.runId || "").trim() &&
            run.status === "succeeded" &&
            Boolean(run.patchArtifactPath),
        ),
      ];

  for (const candidate of preferredCandidates) {
    const patchAbsolutePath = resolvePatchAbsolutePath(candidate.patchArtifactPath!, repoRoot);
    const exists = await access(patchAbsolutePath)
      .then(() => true)
      .catch(() => false);
    if (!exists) continue;

    const patchText = await readFile(patchAbsolutePath, "utf8");
    if (!looksLikeUnifiedDiff(patchText)) continue;

    return {
      run: candidate,
      patchAbsolutePath,
    };
  }

  if (requestedRunId) {
    throw new ProposalApplyError(
      `Execution run "${requestedRunId}" does not contain an applicable git patch artifact.`,
      409,
    );
  }
  throw new ProposalApplyError(
    "No applicable git patch was found in successful execution runs. Re-run execution and ensure it produces a real repository diff.",
    409,
  );
}

export async function applyRewriteProposalPatch(
  input: ApplyRewriteProposalPatchInput,
): Promise<RewriteProposalApply> {
  const proposal = input.proposal;
  const repoRoot = input.repoRoot ? path.resolve(input.repoRoot) : process.cwd();
  if (proposal.status !== "accepted") {
    throw new ProposalApplyError("Only accepted proposals can be applied.", 409);
  }
  if (proposal.apply) {
    throw new ProposalApplyError(
      `This proposal was already applied at ${new Date(proposal.apply.appliedAt).toLocaleString()}.`,
      409,
    );
  }
  if (!isProposalApplyableDiff(proposal.proposedChange.diffPreview)) {
    throw new ProposalApplyError(
      "This proposal is advisory-only (no concrete code-token diff) and is intentionally non-applyable.",
      409,
    );
  }

  const resolved = await resolveApplicableRunPatch(proposal, repoRoot, input.runId);
  const selectedRun = resolved.run;
  const patchAbsolutePath = resolved.patchAbsolutePath;

  const checkResult = await runGitCommand(
    ["apply", "--check", "--whitespace=nowarn", patchAbsolutePath],
    repoRoot,
  );
  if (checkResult.exitCode !== 0) {
    const detail = firstContentLine(checkResult.stderr) || firstContentLine(checkResult.stdout);
    throw new ProposalApplyError(
      detail
        ? `Patch cannot be applied cleanly: ${detail}`
        : "Patch cannot be applied cleanly. Review workspace drift and retry.",
      409,
    );
  }

  const applyResult = await runGitCommand(
    ["apply", "--whitespace=nowarn", patchAbsolutePath],
    repoRoot,
  );
  if (applyResult.exitCode !== 0) {
    const detail = firstContentLine(applyResult.stderr) || firstContentLine(applyResult.stdout);
    throw new ProposalApplyError(
      detail
        ? `git apply failed: ${detail}`
        : "git apply failed while applying the selected patch.",
      409,
    );
  }

  return {
    runId: selectedRun.runId,
    appliedAt: Date.now(),
    appliedBy: normalizePrincipal(input.principalId) || "unknown",
    patchArtifactPath: selectedRun.patchArtifactPath!,
    summary:
      "Patch applied to repository workspace via git apply. Review `git diff` before any commit or push.",
  };
}
