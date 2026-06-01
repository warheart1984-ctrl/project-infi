import { randomUUID } from "crypto";
import { spawn } from "child_process";
import { mkdir, readFile, rm, writeFile } from "fs/promises";
import { existsSync, readdirSync, statSync, type Dirent } from "fs";
import { tmpdir } from "os";
import path from "path";
import type {
  ExecutorProviderSettings,
  RewriteProposal,
  RewriteProposalExecution,
} from "@shared/schema";
import { resolveProposalRoot } from "./proposal-store";

const CODEX_EXECUTION_ENV = "SPIRAL_CODEX_EXECUTION_ENABLED";
const CODEX_EXECUTOR_ENV = "SPIRAL_CODEX_EXECUTOR";
const CODEX_COMMAND_TEMPLATE_ENV = "SPIRAL_CODEX_COMMAND_TEMPLATE";
const CODEX_BINARY_ENV = "SPIRAL_CODEX_BINARY";
const OPENCLAW_COMMAND_TEMPLATE_ENV = "SPIRAL_OPENCLAW_COMMAND_TEMPLATE";
const VERIFY_COMMAND_TEMPLATE_ENV = "SPIRAL_CODEX_VERIFY_COMMAND_TEMPLATE";
const EXECUTION_TIMEOUT_MS_ENV = "SPIRAL_CODEX_EXEC_TIMEOUT_MS";
const WORKTREE_ROOT_ENV = "SPIRAL_CODEX_WORKTREE_ROOT";

type ExecutionMode = "stub" | "codex-cli" | "openclaw-cli";

interface RunRewriteProposalExecutionInput {
  proposal: RewriteProposal;
  principalId: string;
  executorProviderSettings?: ExecutorProviderSettings;
}

interface ShellCommandResult {
  command: string;
  cwd: string;
  exitCode: number;
  stdout: string;
  stderr: string;
  timedOut: boolean;
  durationMs: number;
}

function normalizePrincipal(value: string): string {
  return value.trim().slice(0, 200);
}

function toRepoRelative(filePath: string): string {
  const relative = path.relative(process.cwd(), filePath);
  return relative.split(path.sep).join(path.posix.sep);
}

function formatRunStamp(timestamp: number): string {
  return new Date(timestamp)
    .toISOString()
    .replace(/[:.]/g, "-")
    .replace("T", "_")
    .replace("Z", "");
}

function buildWorktreeDir(runId: string): string {
  const configuredRoot = (process.env[WORKTREE_ROOT_ENV] || "").trim();
  const defaultRoot = process.platform === "win32" ? path.join(tmpdir(), "spwt") : tmpdir();
  const root = configuredRoot || defaultRoot;
  const compactId = runId.replace(/[^a-zA-Z0-9]/g, "").slice(-20) || randomUUID().replace(/-/g, "").slice(0, 20);
  return path.join(root, compactId);
}

export function isCodexExecutionEnabled(): boolean {
  const raw = (process.env[CODEX_EXECUTION_ENV] || "").trim().toLowerCase();
  return raw === "1" || raw === "true" || raw === "yes";
}

function resolveExecutionMode(): ExecutionMode {
  const raw = (process.env[CODEX_EXECUTOR_ENV] || "").trim().toLowerCase();
  if (raw === "stub") return "stub";
  if (raw === "codex" || raw === "codex-cli") return "codex-cli";
  if (raw === "openclaw" || raw === "openclaw-cli") return "openclaw-cli";
  return "codex-cli";
}

function resolveExecutionTimeoutMs(): number {
  const fallback = 15 * 60_000;
  const parsed = Number.parseInt(process.env[EXECUTION_TIMEOUT_MS_ENV] || "", 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(30_000, Math.min(60 * 60_000, parsed));
}

function resolveExecutionEngine(mode: ExecutionMode): RewriteProposalExecution["engine"] {
  switch (mode) {
    case "openclaw-cli":
      return "openclaw-cli";
    case "codex-cli":
      return "codex-cli";
    default:
      return "codex-oauth-stub";
  }
}

function resolveCodexBinaryFromVscodeExtensions(): string | undefined {
  if (process.platform !== "win32") return undefined;
  const home = (process.env.USERPROFILE || process.env.HOME || "").trim();
  if (!home) return undefined;

  const roots = [
    path.join(home, ".vscode", "extensions"),
    path.join(home, ".vscode-insiders", "extensions"),
  ];
  let best: { binaryPath: string; score: number } | undefined;

  for (const root of roots) {
    if (!existsSync(root)) continue;
    let entries: Dirent<string>[];
    try {
      entries = readdirSync(root, { withFileTypes: true, encoding: "utf8" });
    } catch {
      continue;
    }

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (!entry.name.toLowerCase().startsWith("openai.chatgpt-")) continue;
      const binaryPath = path.join(root, entry.name, "bin", "windows-x86_64", "codex.exe");
      if (!existsSync(binaryPath)) continue;
      let score = 0;
      try {
        score = statSync(binaryPath).mtimeMs;
      } catch {
        score = 0;
      }
      if (!best || score > best.score) {
        best = { binaryPath, score };
      }
    }
  }

  return best?.binaryPath;
}

function resolveCodexBinary(): string | undefined {
  const explicit = (process.env[CODEX_BINARY_ENV] || "").trim();
  if (explicit) return explicit;
  return resolveCodexBinaryFromVscodeExtensions();
}

function quoteShellArg(value: string): string {
  if (process.platform === "win32") {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return `'${value.replace(/'/g, `'\\''`)}'`;
}

function buildGitShellCommand(args: string[], cwd: string, options?: { longpaths?: boolean }): string {
  const configTokens = [
    ...(options?.longpaths ? [`-c ${quoteShellArg("core.longpaths=true")}`] : []),
    `-c ${quoteShellArg(`safe.directory=${cwd}`)}`,
  ];
  const argTokens = args.map((arg) => quoteShellArg(arg));
  return ["git", ...configTokens, ...argTokens].join(" ");
}

interface CommandTemplateContext {
  prompt: string;
  promptFile: string;
  workspaceDir: string;
  runDir: string;
  proposalPatchFile: string;
}

function applyCommandTemplate(template: string, context: CommandTemplateContext): string {
  const replacements: Record<string, string> = {
    "{prompt}": quoteShellArg(context.prompt),
    "{promptFile}": quoteShellArg(context.promptFile),
    "{workspace}": quoteShellArg(context.workspaceDir),
    "{runDir}": quoteShellArg(context.runDir),
    "{proposalPatch}": quoteShellArg(context.proposalPatchFile),
  };
  let compiled = template;
  for (const [token, value] of Object.entries(replacements)) {
    compiled = compiled.split(token).join(value);
  }
  return compiled.trim();
}

function resolveExecutionCommand(
  mode: ExecutionMode,
  context: CommandTemplateContext,
): { command?: string; error?: string } {
  if (mode === "stub") {
    return {};
  }

  const template = (() => {
    if (mode === "openclaw-cli") {
      return (process.env[OPENCLAW_COMMAND_TEMPLATE_ENV] || "").trim();
    }
    const configured = (process.env[CODEX_COMMAND_TEMPLATE_ENV] || "").trim();
    if (configured) return configured;
    const binaryPath = resolveCodexBinary();
    return buildDefaultCodexCommandTemplate(binaryPath);
  })();
  if (!template) {
    return {
      error:
        "No OpenClaw command template configured. Set SPIRAL_OPENCLAW_COMMAND_TEMPLATE (for example: openclaw run --prompt-file {promptFile}).",
    };
  }

  const command = applyCommandTemplate(template, context);
  if (!command) {
    return {
      error: "Execution command template produced an empty command.",
    };
  }
  return { command };
}

function buildDefaultCodexCommandTemplate(binaryPath?: string): string {
  const prefix = binaryPath ? quoteShellArg(binaryPath) : "codex";
  return `${prefix} exec --sandbox workspace-write --cd {workspace} {prompt}`;
}

function resolveCodexFallbackCommand(context: CommandTemplateContext): string | undefined {
  const binaryPath = resolveCodexBinary();
  if (!binaryPath) return undefined;
  return applyCommandTemplate(buildDefaultCodexCommandTemplate(binaryPath), context);
}

function isLikelyCommandNotFound(stderr: string, stdout: string): boolean {
  const text = `${stderr}\n${stdout}`.toLowerCase();
  return (
    text.includes("is not recognized as an internal or external command") ||
    text.includes("not recognized as the name of a cmdlet") ||
    text.includes("command not found")
  );
}

function isLikelyUnsupportedApprovalFlag(stderr: string, stdout: string): boolean {
  const text = `${stderr}\n${stdout}`.toLowerCase();
  return (
    text.includes("unexpected argument '--ask-for-approval'") ||
    text.includes('unexpected argument "-a"')
  );
}

function stripUnsupportedApprovalArgs(command: string): string {
  return command
    .replace(/\s--ask-for-approval(?:\s+|=)(?:"[^"]*"|'[^']*'|[^\s"]+)/gi, "")
    .replace(/\s-a(?:\s+|=)(?:"[^"]*"|'[^']*'|[^\s"]+)/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}

async function runShellCommand(
  command: string,
  cwd: string,
  timeoutMs: number,
): Promise<ShellCommandResult> {
  const startedAt = Date.now();
  let stdout = "";
  let stderr = "";
  let timedOut = false;
  let resolved = false;

  return await new Promise((resolve) => {
    const child = spawn(command, {
      cwd,
      shell: true,
      env: process.env,
      windowsHide: true,
    });

    const finish = (exitCode: number) => {
      if (resolved) return;
      resolved = true;
      clearTimeout(timeoutHandle);
      resolve({
        command,
        cwd,
        exitCode,
        stdout,
        stderr,
        timedOut,
        durationMs: Date.now() - startedAt,
      });
    };

    child.stdout?.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr?.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (error: Error) => {
      stderr += `${error.name}: ${error.message}\n`;
      finish(-1);
    });

    child.on("close", (code) => {
      finish(typeof code === "number" ? code : -1);
    });

    const timeoutHandle = setTimeout(() => {
      timedOut = true;
      child.kill();
    }, timeoutMs);
  });
}

function truncateOutput(value: string, limit = 40_000): string {
  if (value.length <= limit) return value;
  return `${value.slice(0, limit)}\n\n[output truncated]`;
}

function summarizeFailureText(stderr: string, stdout: string): string | undefined {
  const candidates = [stderr, stdout]
    .map((value) => value.split(/\r?\n/).map((line) => line.trim()).find(Boolean) || "")
    .filter(Boolean);
  if (candidates.length === 0) return undefined;
  const first = candidates[0];
  return first.length > 180 ? `${first.slice(0, 177)}...` : first;
}

function buildExecutionPrompt(input: RunRewriteProposalExecutionInput): string {
  const proposal = input.proposal;
  const executorProfile = input.executorProviderSettings?.authProfileId?.trim() || "n/a";
  return [
    "Apply this accepted rewrite proposal in the current repository.",
    "Constraints:",
    "- Keep changes minimal and targeted to the proposal.",
    "- Do not commit or push.",
    "- Preserve guardrails and existing behavior unless proposal explicitly changes it.",
    "- Leave final promotion/manual apply to the human reviewer.",
    "- If you cannot modify files, output only a valid unified diff in a ```diff fenced block with diff --git, ---/+++, and @@ line ranges so git apply can consume it.",
    "",
    `Proposal ID: ${proposal.id}`,
    `Chat ID: ${proposal.chatId}`,
    `Executor Auth Profile: ${executorProfile}`,
    `Summary: ${proposal.summary}`,
    `Target: ${proposal.proposedChange.target}`,
    `Kind: ${proposal.proposedChange.kind}`,
    "",
    "Rationale:",
    proposal.proposedChange.rationale,
    "",
    "Diff preview to follow as intent (not mandatory literal patch):",
    proposal.proposedChange.diffPreview,
  ].join("\n");
}

function buildStubExecutionLog(input: RunRewriteProposalExecutionInput, runId: string): string {
  const lines = [
    "Codex execution run (stub mode)",
    `runId: ${runId}`,
    `proposalId: ${input.proposal.id}`,
    `principalId: ${input.principalId}`,
    `chatId: ${input.proposal.chatId}`,
    "",
    "No repository files were modified.",
    "No auto-apply path was used.",
    "Artifacts were prepared for manual Codex/OpenClaw execution handoff.",
  ];
  return lines.join("\n");
}

function buildExecutionLog(entries: string[]): string {
  return entries.filter(Boolean).join("\n");
}

function looksLikeUnifiedDiff(patchText: string): boolean {
  if (!patchText.trim()) return false;
  if (/^diff --git /m.test(patchText) && /^@@\s*-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s*@@/m.test(patchText)) {
    return true;
  }
  const hasHeader = /^---\s+\S+/m.test(patchText) && /^\+\+\+\s+\S+/m.test(patchText);
  const hasHunk = /^@@\s*-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s*@@/m.test(patchText);
  return hasHeader && hasHunk;
}

function collectFencedBlocks(text: string): string[] {
  const blocks: string[] = [];
  const normalized = text.replace(/\r\n/g, "\n");
  const fencePattern = /```(?:diff|patch)?\s*\n([\s\S]*?)```/gi;
  let match: RegExpExecArray | null = null;
  while ((match = fencePattern.exec(normalized)) !== null) {
    const body = (match[1] || "").trim();
    if (body) {
      blocks.push(body);
    }
  }
  return blocks;
}

function extractUnifiedDiffFromRunnerOutput(stdout: string, stderr: string): string | undefined {
  const sources = [stdout, stderr].filter(Boolean);
  for (const source of sources) {
    const normalized = source.replace(/\r\n/g, "\n");
    const candidates = [
      ...collectFencedBlocks(normalized),
      normalized.includes("diff --git ") ? normalized.slice(normalized.indexOf("diff --git ")).trim() : "",
    ].filter(Boolean);
    for (const candidate of candidates) {
      if (!looksLikeUnifiedDiff(candidate)) continue;
      return candidate.endsWith("\n") ? candidate : `${candidate}\n`;
    }
  }
  return undefined;
}

interface SimplePreviewReplacement {
  targetPath: string;
  beforeLine: string;
  afterLine: string;
}

interface SimplePreviewInsertion {
  targetPath: string;
  insertLines: string[];
  anchorHint?: string;
}

function parseSimpleReplacementFromPreview(
  diffPreview: string,
): SimplePreviewReplacement | SimplePreviewInsertion | undefined {
  const lines = diffPreview.split(/\r?\n/);
  const toPathRaw = lines.find((line) => line.startsWith("+++ b/"));
  if (!toPathRaw) return undefined;
  const targetPath = toPathRaw.slice("+++ b/".length).trim();
  if (!targetPath) return undefined;
  const hunkHeader = lines.find((line) => line.startsWith("@@"));
  const anchorHint = hunkHeader
    ? hunkHeader.replace(/^@@\s*/, "").replace(/\s*@@\s*$/, "").trim() || undefined
    : undefined;

  let beforeLine: string | undefined;
  let afterLine: string | undefined;
  const insertLines: string[] = [];
  for (const line of lines) {
    if (!beforeLine && line.startsWith("-") && !line.startsWith("---")) {
      beforeLine = line.slice(1);
      continue;
    }
    if (!afterLine && line.startsWith("+") && !line.startsWith("+++")) {
      afterLine = line.slice(1);
    }
    if (line.startsWith("+") && !line.startsWith("+++")) {
      insertLines.push(line.slice(1));
    }
  }
  if (beforeLine !== undefined && afterLine !== undefined && beforeLine !== afterLine) {
    return {
      targetPath,
      beforeLine,
      afterLine,
    };
  }

  if (beforeLine === undefined && insertLines.length > 0) {
    return {
      targetPath,
      insertLines,
      ...(anchorHint ? { anchorHint } : {}),
    };
  }

  return undefined;
}

function replaceFirstByLineMatch(
  source: string,
  beforeLine: string,
  afterLine: string,
): { next: string; changed: boolean } {
  if (source.includes(beforeLine)) {
    return {
      next: source.replace(beforeLine, afterLine),
      changed: true,
    };
  }

  const eol = source.includes("\r\n") ? "\r\n" : "\n";
  const lines = source.split(/\r?\n/);
  const beforeTrimmed = beforeLine.trim();
  const afterTrimmed = afterLine.trim();
  const splitPunctuation = (value: string): { core: string; suffix: string } => {
    const trimmed = value.trim();
    const match = trimmed.match(/([;,])\s*$/);
    if (!match) {
      return { core: trimmed, suffix: "" };
    }
    return {
      core: trimmed.slice(0, trimmed.length - match[0].length).trimEnd(),
      suffix: match[1],
    };
  };
  const beforeParts = splitPunctuation(beforeTrimmed);
  const afterParts = splitPunctuation(afterTrimmed);
  for (let index = 0; index < lines.length; index += 1) {
    const trimmedCurrent = lines[index].trim();
    const currentParts = splitPunctuation(trimmedCurrent);
    const isExact = trimmedCurrent === beforeTrimmed;
    const isRelaxed = currentParts.core === beforeParts.core;
    if (!isExact && !isRelaxed) continue;
    const leadingWhitespace = lines[index].match(/^\s*/)?.[0] || "";
    const suffix = afterParts.suffix || currentParts.suffix;
    const rewritten = `${leadingWhitespace}${afterParts.core}${suffix}`;
    lines[index] = rewritten;
    return {
      next: lines.join(eol),
      changed: true,
    };
  }

  return {
    next: source,
    changed: false,
  };
}

async function synthesizePatchFromPreview(
  proposal: RewriteProposal,
  workspaceDir: string,
  timeoutMs: number,
): Promise<string | undefined> {
  const parsed = parseSimpleReplacementFromPreview(proposal.proposedChange.diffPreview);
  if (!parsed) return undefined;

  const targetPath = parsed.targetPath.replace(/\//g, path.sep);
  const absolutePath = path.join(workspaceDir, targetPath);
  let current = "";
  try {
    current = await readFile(absolutePath, "utf8");
  } catch {
    return undefined;
  }

  let nextContent = current;
  let changed = false;

  if ("beforeLine" in parsed) {
    const updated = replaceFirstByLineMatch(current, parsed.beforeLine, parsed.afterLine);
    nextContent = updated.next;
    changed = updated.changed && updated.next !== current;
  } else {
    const eol = current.includes("\r\n") ? "\r\n" : "\n";
    const fileLines = current.split(/\r?\n/);
    const alreadyPresent = parsed.insertLines.every((line) => current.includes(line.trim()));
    if (!alreadyPresent) {
      let insertAt = -1;
      if (parsed.anchorHint) {
        const hint = parsed.anchorHint.toLowerCase();
        insertAt = fileLines.findIndex((line) => line.toLowerCase().includes(hint));
      }
      if (insertAt < 0) {
        insertAt = fileLines.findIndex((line) => /^\s*type\s+[A-Za-z0-9_]+\s*=/.test(line));
      }
      if (insertAt < 0) {
        insertAt = fileLines.length > 0 ? fileLines.length - 1 : 0;
      }
      const block = parsed.insertLines.map((line) => line.trimEnd());
      fileLines.splice(insertAt, 0, ...block);
      nextContent = fileLines.join(eol);
      changed = nextContent !== current;
    }
  }

  if (!changed) {
    return undefined;
  }

  await writeFile(absolutePath, nextContent, "utf8");
  const diffCommand = buildGitShellCommand(["diff", "--no-color", "--", parsed.targetPath], workspaceDir);
  const diffResult = await runShellCommand(diffCommand, workspaceDir, timeoutMs);
  if (diffResult.exitCode !== 0 || !diffResult.stdout.trim()) {
    return undefined;
  }
  return diffResult.stdout;
}

export async function runRewriteProposalExecution(
  input: RunRewriteProposalExecutionInput,
): Promise<RewriteProposalExecution> {
  const executedAt = Date.now();
  const runId = `${formatRunStamp(executedAt)}-${randomUUID()}`;
  const mode = resolveExecutionMode();
  const engine = resolveExecutionEngine(mode);
  const timeoutMs = resolveExecutionTimeoutMs();
  const runDir = path.join(resolveProposalRoot(), "executions", input.proposal.id, runId);
  await mkdir(runDir, { recursive: true });

  const requestPath = path.join(runDir, "request.json");
  const proposalPatchPath = path.join(runDir, "proposal.patch");
  const generatedPatchPath = path.join(runDir, "generated.patch");
  const promptPath = path.join(runDir, "prompt.txt");
  const logPath = path.join(runDir, "execution.log");
  const prompt = buildExecutionPrompt(input);
  const requestPayload = {
    runId,
    executedAt,
    mode,
    engine,
    proposal: {
      id: input.proposal.id,
      summary: input.proposal.summary,
      signal: input.proposal.signal,
      proposedChange: input.proposal.proposedChange,
    },
    safety: {
      autoApply: false,
      isolation: mode === "stub" ? "proposal-artifacts-only" : "detached-git-worktree",
      requiresHumanPromotion: true,
    },
  };

  await Promise.all([
    writeFile(requestPath, JSON.stringify(requestPayload, null, 2), "utf8"),
    writeFile(proposalPatchPath, input.proposal.proposedChange.diffPreview, "utf8"),
    writeFile(promptPath, prompt, "utf8"),
  ]);

  if (mode === "stub") {
    await Promise.all([
      writeFile(generatedPatchPath, input.proposal.proposedChange.diffPreview, "utf8"),
      writeFile(logPath, buildStubExecutionLog(input, runId), "utf8"),
    ]);
    return {
      runId,
      status: "succeeded",
      engine,
      executedAt,
      executedBy: normalizePrincipal(input.principalId) || "unknown",
      summary:
        "Execution artifacts prepared in an isolated proposal run directory. Manual review and manual apply remain required.",
      logArtifactPath: toRepoRelative(logPath),
      patchArtifactPath: toRepoRelative(generatedPatchPath),
    };
  }

  const logLines: string[] = [];
  let workspaceDir: string | null = null;
  let commandUsed = "";
  let exitCode = -1;
  let status: RewriteProposalExecution["status"] = "failed";
  let summary =
    "Execution did not complete. Review execution artifacts and runner configuration before retrying.";
  let generatedPatch = "";

  logLines.push(`Execution mode: ${mode}`);
  logLines.push(`Engine: ${engine}`);
  logLines.push(`Run ID: ${runId}`);
  logLines.push(`Timeout (ms): ${timeoutMs}`);

  try {
    workspaceDir = buildWorktreeDir(runId);
    await mkdir(path.dirname(workspaceDir), { recursive: true });
    await rm(workspaceDir, { recursive: true, force: true }).catch(() => {
      // Ignore stale cleanup errors.
    });
    const addWorktreeCommand = buildGitShellCommand(
      ["worktree", "add", "--detach", workspaceDir, "HEAD"],
      process.cwd(),
      { longpaths: true },
    );
    const addResult = await runShellCommand(addWorktreeCommand, process.cwd(), timeoutMs);
    logLines.push("");
    logLines.push("[git-worktree:add]");
    logLines.push(`command: ${addResult.command}`);
    logLines.push(`exitCode: ${addResult.exitCode}`);
    logLines.push(`durationMs: ${addResult.durationMs}`);
    if (addResult.stdout.trim()) {
      logLines.push("stdout:");
      logLines.push(truncateOutput(addResult.stdout));
    }
    if (addResult.stderr.trim()) {
      logLines.push("stderr:");
      logLines.push(truncateOutput(addResult.stderr));
    }
    if (addResult.exitCode !== 0) {
      throw new Error("Could not create isolated git worktree for execution.");
    }

    const commandContext: CommandTemplateContext = {
      prompt,
      promptFile: promptPath,
      workspaceDir,
      runDir,
      proposalPatchFile: proposalPatchPath,
    };
    const resolved = resolveExecutionCommand(mode, commandContext);
    if (!resolved.command) {
      throw new Error(resolved.error || "Execution command is not configured.");
    }
    commandUsed = resolved.command;

    let runResult = await runShellCommand(commandUsed, workspaceDir, timeoutMs);
    logLines.push("");
    logLines.push("[runner]");
    logLines.push(`command: ${runResult.command}`);
    logLines.push(`cwd: ${runResult.cwd}`);
    logLines.push(`exitCode: ${runResult.exitCode}`);
    logLines.push(`timedOut: ${runResult.timedOut}`);
    logLines.push(`durationMs: ${runResult.durationMs}`);
    if (runResult.stdout.trim()) {
      logLines.push("stdout:");
      logLines.push(truncateOutput(runResult.stdout));
    }
    if (runResult.stderr.trim()) {
      logLines.push("stderr:");
      logLines.push(truncateOutput(runResult.stderr));
    }

    if (
      mode === "codex-cli" &&
      runResult.exitCode !== 0 &&
      isLikelyCommandNotFound(runResult.stderr, runResult.stdout)
    ) {
      const fallbackCommand = resolveCodexFallbackCommand(commandContext);
      if (fallbackCommand && fallbackCommand !== commandUsed) {
        const fallbackResult = await runShellCommand(fallbackCommand, workspaceDir, timeoutMs);
        logLines.push("");
        logLines.push("[runner:fallback]");
        logLines.push(`command: ${fallbackResult.command}`);
        logLines.push(`cwd: ${fallbackResult.cwd}`);
        logLines.push(`exitCode: ${fallbackResult.exitCode}`);
        logLines.push(`timedOut: ${fallbackResult.timedOut}`);
        logLines.push(`durationMs: ${fallbackResult.durationMs}`);
        if (fallbackResult.stdout.trim()) {
          logLines.push("stdout:");
          logLines.push(truncateOutput(fallbackResult.stdout));
        }
        if (fallbackResult.stderr.trim()) {
          logLines.push("stderr:");
          logLines.push(truncateOutput(fallbackResult.stderr));
        }
        runResult = fallbackResult;
        commandUsed = fallbackCommand;
      }
    }

    if (
      mode === "codex-cli" &&
      runResult.exitCode !== 0 &&
      isLikelyUnsupportedApprovalFlag(runResult.stderr, runResult.stdout)
    ) {
      const sanitizedCommand = stripUnsupportedApprovalArgs(commandUsed);
      if (sanitizedCommand && sanitizedCommand !== commandUsed) {
        const compatibilityResult = await runShellCommand(sanitizedCommand, workspaceDir, timeoutMs);
        logLines.push("");
        logLines.push("[runner:compat-approval-flag]");
        logLines.push(`command: ${compatibilityResult.command}`);
        logLines.push(`cwd: ${compatibilityResult.cwd}`);
        logLines.push(`exitCode: ${compatibilityResult.exitCode}`);
        logLines.push(`timedOut: ${compatibilityResult.timedOut}`);
        logLines.push(`durationMs: ${compatibilityResult.durationMs}`);
        if (compatibilityResult.stdout.trim()) {
          logLines.push("stdout:");
          logLines.push(truncateOutput(compatibilityResult.stdout));
        }
        if (compatibilityResult.stderr.trim()) {
          logLines.push("stderr:");
          logLines.push(truncateOutput(compatibilityResult.stderr));
        }
        runResult = compatibilityResult;
        commandUsed = sanitizedCommand;
      }
    }

    exitCode = runResult.exitCode;

    const verifyTemplate = (process.env[VERIFY_COMMAND_TEMPLATE_ENV] || "").trim();
    let verifyResult: ShellCommandResult | undefined;
    if (verifyTemplate) {
      const verifyCommand = applyCommandTemplate(verifyTemplate, {
        prompt,
        promptFile: promptPath,
        workspaceDir,
        runDir,
        proposalPatchFile: proposalPatchPath,
      });
      verifyResult = await runShellCommand(verifyCommand, workspaceDir, timeoutMs);
      logLines.push("");
      logLines.push("[verify]");
      logLines.push(`command: ${verifyResult.command}`);
      logLines.push(`exitCode: ${verifyResult.exitCode}`);
      logLines.push(`timedOut: ${verifyResult.timedOut}`);
      logLines.push(`durationMs: ${verifyResult.durationMs}`);
      if (verifyResult.stdout.trim()) {
        logLines.push("stdout:");
        logLines.push(truncateOutput(verifyResult.stdout));
      }
      if (verifyResult.stderr.trim()) {
        logLines.push("stderr:");
        logLines.push(truncateOutput(verifyResult.stderr));
      }
    }

    const diffResult = await runShellCommand(
      buildGitShellCommand(["diff", "--no-color"], workspaceDir),
      workspaceDir,
      timeoutMs,
    );
    logLines.push("");
    logLines.push("[git-diff]");
    logLines.push(`exitCode: ${diffResult.exitCode}`);
    logLines.push(`durationMs: ${diffResult.durationMs}`);
    let hasRepoDiff = Boolean(diffResult.stdout.trim());
    if (hasRepoDiff) {
      generatedPatch = diffResult.stdout;
    }
    if (diffResult.stderr.trim()) {
      logLines.push("stderr:");
      logLines.push(truncateOutput(diffResult.stderr));
    }

    if (!hasRepoDiff) {
      const runnerOutputPatch = extractUnifiedDiffFromRunnerOutput(runResult.stdout, runResult.stderr);
      if (runnerOutputPatch) {
        generatedPatch = runnerOutputPatch;
        hasRepoDiff = true;
        logLines.push("");
        logLines.push("[fallback:runner-output-patch]");
        logLines.push("Captured a valid unified diff from runner output because runner produced no git diff.");
      }
    }

    if (!hasRepoDiff) {
      const synthesized = await synthesizePatchFromPreview(input.proposal, workspaceDir, timeoutMs);
      if (synthesized) {
        generatedPatch = synthesized;
        hasRepoDiff = true;
        logLines.push("");
        logLines.push("[fallback:proposal-preview]");
        logLines.push("Synthesized a repository patch from proposal diffPreview because runner produced no git diff.");
      }
    }

    const verificationFailed = Boolean(verifyResult && verifyResult.exitCode !== 0);
    const runnerReportedSuccess = runResult.exitCode === 0 && !verificationFailed;
    status = runnerReportedSuccess && hasRepoDiff ? "succeeded" : "failed";
    const failureDetail = summarizeFailureText(runResult.stderr, runResult.stdout);
    summary =
      status === "succeeded" && hasRepoDiff && Boolean(diffResult.stdout.trim())
        ? "Runner completed in isolated worktree; review generated patch and logs before any manual apply."
      : status === "succeeded"
        ? "Runner completed in isolated worktree and produced a deterministic patch fallback from proposal intent; review artifacts before any manual apply."
        : runnerReportedSuccess && !hasRepoDiff
          ? "Runner completed but produced no repository diff. No patch is available to apply."
        : failureDetail
          ? `Runner reported a failure: ${failureDetail}`
          : "Runner reported a failure; inspect execution log and artifacts before retrying.";
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown execution error";
    logLines.push("");
    logLines.push("[error]");
    logLines.push(message);
    status = "failed";
    summary = `Execution failed before completion: ${message}`;
  } finally {
    await writeFile(generatedPatchPath, generatedPatch, "utf8");
    if (workspaceDir) {
      const removeResult = await runShellCommand(
        buildGitShellCommand(
          ["worktree", "remove", "--force", workspaceDir],
          process.cwd(),
          { longpaths: true },
        ),
        process.cwd(),
        timeoutMs,
      );
      logLines.push("");
      logLines.push("[git-worktree:remove]");
      logLines.push(`command: ${removeResult.command}`);
      logLines.push(`exitCode: ${removeResult.exitCode}`);
      logLines.push(`durationMs: ${removeResult.durationMs}`);
      if (removeResult.stderr.trim()) {
        logLines.push("stderr:");
        logLines.push(truncateOutput(removeResult.stderr));
      }
      await rm(workspaceDir, { recursive: true, force: true }).catch(() => {
        // Worktree removal may already remove the directory.
      });
    }
    await writeFile(logPath, buildExecutionLog(logLines), "utf8");
  }

  return {
    runId,
    status,
    engine,
    executedAt,
    executedBy: normalizePrincipal(input.principalId) || "unknown",
    summary,
    ...(commandUsed ? { command: commandUsed.slice(0, 1000) } : {}),
    ...(exitCode >= -1 ? { exitCode } : {}),
    logArtifactPath: toRepoRelative(logPath),
    patchArtifactPath: toRepoRelative(generatedPatchPath),
  };
}
