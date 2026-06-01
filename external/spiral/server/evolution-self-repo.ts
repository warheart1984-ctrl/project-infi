import { spawn } from "child_process";
import { existsSync } from "fs";
import { mkdir, readFile, writeFile, copyFile, rm } from "fs/promises";
import path from "path";
import type { EvolutionMode, EvolutionTrigger } from "./evolution-state";

const SELF_REPO_DIR = path.join(process.cwd(), ".spiral-self");
const SELF_REPO_MIRROR_DIR = path.join(SELF_REPO_DIR, "mirror");
const SELF_REPO_PATCH_DIR = path.join(SELF_REPO_DIR, "patches");
const SELF_REPO_CYCLE_DIR = path.join(SELF_REPO_DIR, "cycles");

export interface EvolutionDriftIndex {
  filesTouched: number;
  linesAdded: number;
  linesDeleted: number;
  semanticDiffScore: number;
  invariantImpact: "none" | "low" | "medium" | "high";
}

interface PatchSummary {
  files: string[];
  linesAdded: number;
  linesDeleted: number;
}

interface GitCommandResult {
  exitCode: number;
  stdout: string;
  stderr: string;
}

export interface SelfRepoCommitInput {
  principalId: string;
  proposalId: string;
  chatId: string;
  mode: EvolutionMode;
  trigger: EvolutionTrigger;
  signal?: string;
  timestamp: number;
  patchArtifactPath: string;
  executionSummary: string;
  applySummary: string;
}

export interface SelfRepoCommitResult {
  cycleId: number;
  commitHash: string;
  driftIndex: EvolutionDriftIndex;
  files: string[];
  repoPath: string;
}

function normalizeTimestamp(value: number): number {
  if (!Number.isFinite(value)) return Date.now();
  return Math.max(1, Math.floor(value));
}

function stableStringify(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) {
    return `[${value.map((entry) => stableStringify(entry)).join(",")}]`;
  }
  const entries = Object.entries(value as Record<string, unknown>).sort((a, b) =>
    a[0].localeCompare(b[0]),
  );
  return `{${entries
    .map(([key, nested]) => `${JSON.stringify(key)}:${stableStringify(nested)}`)
    .join(",")}}`;
}

async function runGitCommand(args: string[], cwd: string): Promise<GitCommandResult> {
  return await new Promise((resolve) => {
    const child = spawn("git", args, {
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

function normalizePatchRelativePath(value: string): string {
  return value.replace(/^\.?[\\/]+/, "").replace(/\\/g, "/").trim();
}

export function summarizePatchFromText(patchText: string): PatchSummary {
  const files = new Set<string>();
  let linesAdded = 0;
  let linesDeleted = 0;
  for (const rawLine of patchText.split(/\r?\n/g)) {
    const line = rawLine.trimEnd();
    const plusMatch = line.match(/^\+\+\+\s+b\/(.+)$/);
    if (plusMatch?.[1] && plusMatch[1] !== "/dev/null") {
      files.add(normalizePatchRelativePath(plusMatch[1]));
      continue;
    }
    const minusMatch = line.match(/^---\s+a\/(.+)$/);
    if (minusMatch?.[1] && minusMatch[1] !== "/dev/null") {
      files.add(normalizePatchRelativePath(minusMatch[1]));
      continue;
    }
    if (line.startsWith("+") && !line.startsWith("+++")) {
      linesAdded += 1;
      continue;
    }
    if (line.startsWith("-") && !line.startsWith("---")) {
      linesDeleted += 1;
    }
  }
  return {
    files: Array.from(files).sort((a, b) => a.localeCompare(b)),
    linesAdded,
    linesDeleted,
  };
}

function invariantImpactFromFiles(files: string[]): EvolutionDriftIndex["invariantImpact"] {
  if (files.length === 0) return "none";
  const highPatterns = [
    /^server\/routes\.ts$/i,
    /^server\/veil-channel\.mirror\.ts$/i,
    /^server\/memory-rotation(?:-adaptive|-shadow)?\.ts$/i,
    /^server\/memory-scoring\.ts$/i,
    /^server\/shared\//i,
    /^shared\/schema\.ts$/i,
  ];
  const mediumPatterns = [
    /^server\//i,
    /^shared\//i,
    /^script\//i,
  ];
  if (files.some((file) => highPatterns.some((pattern) => pattern.test(file)))) {
    return "high";
  }
  if (files.some((file) => mediumPatterns.some((pattern) => pattern.test(file)))) {
    return "medium";
  }
  return "low";
}

function semanticDiffScore(linesAdded: number, linesDeleted: number, filesTouched: number): number {
  const lineMass = linesAdded + linesDeleted;
  if (lineMass <= 0 || filesTouched <= 0) return 0;
  const fileFactor = Math.min(1, filesTouched / 12);
  const lineFactor = Math.min(1, lineMass / 240);
  return Number((0.4 * fileFactor + 0.6 * lineFactor).toFixed(6));
}

function buildDriftIndex(summary: PatchSummary): EvolutionDriftIndex {
  return {
    filesTouched: summary.files.length,
    linesAdded: summary.linesAdded,
    linesDeleted: summary.linesDeleted,
    semanticDiffScore: semanticDiffScore(summary.linesAdded, summary.linesDeleted, summary.files.length),
    invariantImpact: invariantImpactFromFiles(summary.files),
  };
}

async function ensureSelfRepoInitialized(): Promise<void> {
  await mkdir(SELF_REPO_DIR, { recursive: true });
  await mkdir(SELF_REPO_MIRROR_DIR, { recursive: true });
  await mkdir(SELF_REPO_PATCH_DIR, { recursive: true });
  await mkdir(SELF_REPO_CYCLE_DIR, { recursive: true });

  if (!existsSync(path.join(SELF_REPO_DIR, ".git"))) {
    const init = await runGitCommand(["init"], SELF_REPO_DIR);
    if (init.exitCode !== 0) {
      throw new Error(`Failed to initialize .spiral-self git repo: ${init.stderr || init.stdout}`.trim());
    }
  }

  const nameCheck = await runGitCommand(["config", "--get", "user.name"], SELF_REPO_DIR);
  if (nameCheck.exitCode !== 0 || !nameCheck.stdout.trim()) {
    await runGitCommand(["config", "user.name", "Spiral Self"], SELF_REPO_DIR);
  }
  const emailCheck = await runGitCommand(["config", "--get", "user.email"], SELF_REPO_DIR);
  if (emailCheck.exitCode !== 0 || !emailCheck.stdout.trim()) {
    await runGitCommand(["config", "user.email", "spiral-self@local"], SELF_REPO_DIR);
  }
}

async function resolveNextCycleId(): Promise<number> {
  const count = await runGitCommand(["rev-list", "--count", "HEAD"], SELF_REPO_DIR);
  if (count.exitCode !== 0) return 1;
  const parsed = Number.parseInt(count.stdout.trim(), 10);
  if (!Number.isFinite(parsed) || parsed < 0) return 1;
  return parsed + 1;
}

function resolveRootRelativeFile(value: string): string {
  const normalized = normalizePatchRelativePath(value);
  if (!normalized) return "";
  const relative = path.relative(process.cwd(), path.resolve(process.cwd(), normalized));
  const asPosix = relative.split(path.sep).join("/");
  if (!asPosix || asPosix.startsWith("..") || path.isAbsolute(asPosix)) return "";
  return asPosix;
}

async function mirrorFileIntoSelfRepo(relativeFile: string): Promise<void> {
  const sourcePath = path.resolve(process.cwd(), relativeFile);
  const targetPath = path.resolve(SELF_REPO_MIRROR_DIR, relativeFile);
  const relativeToMirror = path.relative(SELF_REPO_MIRROR_DIR, targetPath);
  if (relativeToMirror.startsWith("..") || path.isAbsolute(relativeToMirror)) {
    throw new Error(`Refusing to mirror file outside self repo: ${relativeFile}`);
  }
  if (!existsSync(sourcePath)) {
    await rm(targetPath, { force: true });
    return;
  }
  await mkdir(path.dirname(targetPath), { recursive: true });
  await copyFile(sourcePath, targetPath);
}

async function hasStagedChanges(): Promise<boolean> {
  const diff = await runGitCommand(["diff", "--cached", "--quiet"], SELF_REPO_DIR);
  return diff.exitCode === 1;
}

async function resolveHeadHash(): Promise<string> {
  const head = await runGitCommand(["rev-parse", "--short", "HEAD"], SELF_REPO_DIR);
  if (head.exitCode !== 0) {
    throw new Error(`Failed to resolve self-repo commit hash: ${head.stderr || head.stdout}`.trim());
  }
  const hash = head.stdout.trim();
  if (!hash) {
    throw new Error("Self-repo commit hash was empty.");
  }
  return hash;
}

export async function recordSelfRepoCommit(input: SelfRepoCommitInput): Promise<SelfRepoCommitResult> {
  await ensureSelfRepoInitialized();
  const timestamp = normalizeTimestamp(input.timestamp);
  const patchAbsolutePath = path.resolve(process.cwd(), input.patchArtifactPath);
  if (!existsSync(patchAbsolutePath)) {
    throw new Error(`Patch artifact not found for self-repo commit: ${input.patchArtifactPath}`);
  }
  const patchText = await readFile(patchAbsolutePath, "utf8");
  const patchSummary = summarizePatchFromText(patchText);
  const files = patchSummary.files
    .map((file) => resolveRootRelativeFile(file))
    .filter(Boolean)
    .sort((a, b) => a.localeCompare(b));

  const cycleId = await resolveNextCycleId();
  const driftIndex = buildDriftIndex({ ...patchSummary, files });
  const patchTargetName = `cycle-${cycleId}.patch`;
  const patchTargetRelative = path.posix.join("patches", patchTargetName);
  const patchTargetAbsolute = path.join(SELF_REPO_DIR, patchTargetRelative);
  await mkdir(path.dirname(patchTargetAbsolute), { recursive: true });
  await writeFile(patchTargetAbsolute, patchText, "utf8");

  for (const file of files) {
    await mirrorFileIntoSelfRepo(file);
  }

  const cycleRecord = {
    schemaVersion: "evolution-self-cycle.v1",
    cycleId,
    timestamp,
    principalId: input.principalId.trim().slice(0, 200),
    proposalId: input.proposalId.trim().slice(0, 120),
    chatId: input.chatId.trim().slice(0, 200),
    mode: input.mode,
    trigger: input.trigger,
    ...(input.signal && input.signal.trim() ? { signal: input.signal.trim().slice(0, 280) } : {}),
    patchArtifactPath: normalizePatchRelativePath(input.patchArtifactPath),
    executionSummary: input.executionSummary.trim().slice(0, 2000),
    applySummary: input.applySummary.trim().slice(0, 2000),
    driftIndex,
    files,
  };
  const cycleFileRelative = path.posix.join("cycles", `cycle-${cycleId}.json`);
  const cycleFileAbsolute = path.join(SELF_REPO_DIR, cycleFileRelative);
  await mkdir(path.dirname(cycleFileAbsolute), { recursive: true });
  await writeFile(cycleFileAbsolute, `${stableStringify(cycleRecord)}\n`, "utf8");

  const addPaths = [
    patchTargetRelative,
    cycleFileRelative,
    ...files.map((file) => path.posix.join("mirror", file)),
  ];
  const add = await runGitCommand(["add", "--all", "--", ...addPaths], SELF_REPO_DIR);
  if (add.exitCode !== 0) {
    throw new Error(`Failed to stage self-repo files: ${add.stderr || add.stdout}`.trim());
  }
  if (!(await hasStagedChanges())) {
    throw new Error("Self-repo commit aborted: no staged changes.");
  }

  const messageTitle = `cycle-${cycleId} ${input.mode.toUpperCase()} ${input.proposalId.trim().slice(0, 12)}`;
  const messageBody = [
    `mode=${input.mode}`,
    `trigger=${input.trigger}`,
    `proposal=${input.proposalId.trim()}`,
    `chat=${input.chatId.trim()}`,
    ...(input.signal && input.signal.trim() ? [`signal=${input.signal.trim().slice(0, 280)}`] : []),
    `drift.files=${driftIndex.filesTouched}`,
    `drift.added=${driftIndex.linesAdded}`,
    `drift.deleted=${driftIndex.linesDeleted}`,
    `drift.semantic=${driftIndex.semanticDiffScore.toFixed(6)}`,
    `drift.invariantImpact=${driftIndex.invariantImpact}`,
  ].join("\n");
  const commit = await runGitCommand(["commit", "-m", messageTitle, "-m", messageBody], SELF_REPO_DIR);
  if (commit.exitCode !== 0) {
    throw new Error(`Failed to create self-repo commit: ${commit.stderr || commit.stdout}`.trim());
  }

  const commitHash = await resolveHeadHash();
  return {
    cycleId,
    commitHash,
    driftIndex,
    files,
    repoPath: SELF_REPO_DIR,
  };
}
