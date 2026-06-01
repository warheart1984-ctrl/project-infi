import { execFileSync } from "child_process";
import { readFile, readdir } from "fs/promises";
import path from "path";
import { getSelfInspectionIndex } from "./self-inspection";

type EvaluationClass = "Rule" | "Contract";
export type SelfEvaluationProfile = "integrity" | "gates" | "contracts" | "all";

export interface SelfEvaluationCheck {
  id: string;
  class: EvaluationClass;
  pass: boolean;
  detail: string;
  evidence: string[];
}

export interface SelfEvaluationReport {
  profile: SelfEvaluationProfile;
  generatedAt: string;
  gitCommit: string | null;
  summary: {
    total: number;
    passed: number;
    failed: number;
  };
  checks: SelfEvaluationCheck[];
}

const PROFILE_SET = new Set<SelfEvaluationProfile>(["integrity", "gates", "contracts", "all"]);

function normalizeWorkspacePath(value: string): string {
  return value.split(path.sep).join("/");
}

function buildCheck(
  id: string,
  className: EvaluationClass,
  pass: boolean,
  detail: string,
  evidence: string[],
): SelfEvaluationCheck {
  return {
    id,
    class: className,
    pass,
    detail,
    evidence,
  };
}

async function readWorkspaceFile(rootDir: string, relativePath: string): Promise<string> {
  return await readFile(path.join(rootDir, relativePath), "utf8");
}

function resolveActiveVeilModulePathFromIndexSource(indexSource: string): string {
  const importMatch = indexSource.match(
    /import\s*\{\s*setupVeilChannel\s*\}\s*from\s*["']([^"']+)["'];?/,
  );
  const moduleSpecifier = (importMatch?.[1] || "./veil-channel.mirror").trim();
  if (!moduleSpecifier.startsWith("./")) {
    return "server/veil-channel.mirror.ts";
  }

  const modulePath = moduleSpecifier.slice(2);
  if (!modulePath) return "server/veil-channel.mirror.ts";
  if (modulePath.endsWith(".ts")) return normalizeWorkspacePath(`server/${modulePath}`);
  return normalizeWorkspacePath(`server/${modulePath}.ts`);
}

async function resolveActiveVeilModulePath(rootDir: string): Promise<string> {
  try {
    const indexSource = await readWorkspaceFile(rootDir, "server/index.ts");
    return resolveActiveVeilModulePathFromIndexSource(indexSource);
  } catch {
    return "server/veil-channel.mirror.ts";
  }
}

async function checkSharedSelfInspectDispatcher(
  rootDir: string,
  activeVeilModulePath: string,
): Promise<SelfEvaluationCheck> {
  const [routesSource, veilSource] = await Promise.all([
    readWorkspaceFile(rootDir, "server/routes.ts"),
    readWorkspaceFile(rootDir, activeVeilModulePath),
  ]);

  const routesImportsShared =
    /from\s+["']\.\/self-inspection-command["']/.test(routesSource) &&
    /\bparseSelfInspectCommand\b/.test(routesSource) &&
    /\bexecuteSelfInspectCommand\b/.test(routesSource);
  const veilImportsShared =
    /from\s+["']\.\/self-inspection-command["']/.test(veilSource) &&
    /\bparseSelfInspectCommand\b/.test(veilSource) &&
    /\bexecuteSelfInspectCommand\b/.test(veilSource);
  const routesHasSingleParseCall =
    (routesSource.match(/parseSelfInspectCommand\(message\)/g) || []).length === 1;
  const veilHasSingleParseCall =
    (veilSource.match(/parseSelfInspectCommand\(invocation\.utterance\)/g) || []).length === 1;
  const routesHasLocalOverride = /\bfunction\s+parseSelfInspectCommand\s*\(/.test(routesSource);
  const veilHasLocalOverride = /\bfunction\s+parseSelfInspectCommand\s*\(/.test(veilSource);

  const pass =
    routesImportsShared &&
    veilImportsShared &&
    routesHasSingleParseCall &&
    veilHasSingleParseCall &&
    !routesHasLocalOverride &&
    !veilHasLocalOverride;

  const evidence = [
    `veil.module=${activeVeilModulePath}`,
    `routes.import.shared=${routesImportsShared ? "yes" : "no"}`,
    `veil.import.shared=${veilImportsShared ? "yes" : "no"}`,
    `routes.parse.calls=${(routesSource.match(/parseSelfInspectCommand\(message\)/g) || []).length}`,
    `veil.parse.calls=${(veilSource.match(/parseSelfInspectCommand\(invocation\.utterance\)/g) || []).length}`,
    `routes.local.override=${routesHasLocalOverride ? "yes" : "no"}`,
    `veil.local.override=${veilHasLocalOverride ? "yes" : "no"}`,
  ];

  return buildCheck(
    "shared-self-inspect-dispatcher",
    "Rule",
    pass,
    "Both invocation surfaces route through shared self-inspection command machinery.",
    evidence,
  );
}

async function checkNoShadowSelfInspectExecutors(
  rootDir: string,
  activeVeilModulePath: string,
): Promise<SelfEvaluationCheck> {
  const index = await getSelfInspectionIndex({
    rootDir,
    includeDirs: ["server"],
    forceRefresh: true,
  });
  const sharedImporterFiles: string[] = [];
  const parseCallCounts = new Map<string, number>();
  const executeCallCounts = new Map<string, number>();

  for (const file of index.files) {
    if (!file.path.startsWith("server/")) continue;
    const source = await readWorkspaceFile(rootDir, file.path);
    if (/from\s+["']\.\/self-inspection-command["']/.test(source)) {
      sharedImporterFiles.push(file.path);
      parseCallCounts.set(file.path, (source.match(/\bparseSelfInspectCommand\s*\(/g) || []).length);
      executeCallCounts.set(file.path, (source.match(/\bexecuteSelfInspectCommand\s*\(/g) || []).length);
    }
  }

  sharedImporterFiles.sort((a, b) => a.localeCompare(b));
  const expectedCallerSet = new Set(["server/routes.ts", activeVeilModulePath]);
  const importersMatchExpected =
    sharedImporterFiles.length === expectedCallerSet.size &&
    sharedImporterFiles.every((pathValue) => expectedCallerSet.has(pathValue));

  const expectedSingleCalls = sharedImporterFiles.every((pathValue) => {
    const parseCount = parseCallCounts.get(pathValue) || 0;
    const executeCount = executeCallCounts.get(pathValue) || 0;
    return parseCount === 1 && executeCount === 1;
  });

  const pass = importersMatchExpected && expectedSingleCalls;

  return buildCheck(
    "no-shadow-self-inspect-dispatchers",
    "Rule",
    pass,
    "No alternate self-inspection dispatcher/executor paths exist outside the approved surfaces.",
    [
      `veil.module=${activeVeilModulePath}`,
      `shared.importers=${sharedImporterFiles.join(",") || "(none)"}`,
      ...sharedImporterFiles.map((pathValue) => {
        const parseCount = parseCallCounts.get(pathValue) || 0;
        const executeCount = executeCallCounts.get(pathValue) || 0;
        return `${pathValue}: parse.calls=${parseCount} execute.calls=${executeCount}`;
      }),
    ],
  );
}

async function checkSelfInspectGatePrecedence(
  rootDir: string,
  activeVeilModulePath: string,
): Promise<SelfEvaluationCheck> {
  const [routesSource, veilSource] = await Promise.all([
    readWorkspaceFile(rootDir, "server/routes.ts"),
    readWorkspaceFile(rootDir, activeVeilModulePath),
  ]);

  const routesGateIndex = routesSource.indexOf("if (!invocationGate.allowed)");
  const routesSelfInspectIndex = routesSource.indexOf(
    "const selfInspectCommand = parseSelfInspectCommand(message);",
  );
  const routesMemoryIndex = routesSource.indexOf("const memoryCommand = parseMemoryCommand(message);");
  const routesPromptIndex = routesSource.indexOf("const promptMetadata = await detectPromptMetadata(");
  const routesOrderOk =
    routesGateIndex >= 0 &&
    routesSelfInspectIndex > routesGateIndex &&
    routesMemoryIndex > routesSelfInspectIndex &&
    routesPromptIndex > routesMemoryIndex;

  const veilGateIndex = veilSource.indexOf("if (!gateResult.allowed && !thresholdBypass)");
  const veilSelfInspectIndex = veilSource.indexOf(
    "const selfInspectCommand = parseSelfInspectCommand(invocation.utterance);",
  );
  const veilMemoryIndex = veilSource.indexOf("const memoryCommand = parseMemoryCommand(invocation.utterance);");
  const veilModelIndex = veilSource.indexOf("const whisper = await buildInvocationReply(");
  const veilOrderOk =
    veilGateIndex >= 0 &&
    veilSelfInspectIndex > veilGateIndex &&
    veilMemoryIndex > veilSelfInspectIndex &&
    veilModelIndex > veilMemoryIndex;

  return buildCheck(
    "inspection-dispatch-precedes-recall",
    "Contract",
    routesOrderOk && veilOrderOk,
    "Gate checks run before self-inspection; self-inspection runs before memory recall and LLM generation.",
    [
      `routes.order=${routesOrderOk ? "ok" : "invalid"} gate:${routesGateIndex} self:${routesSelfInspectIndex} memory:${routesMemoryIndex} prompt:${routesPromptIndex}`,
      `veil.module=${activeVeilModulePath}`,
      `veil.order=${veilOrderOk ? "ok" : "invalid"} gate:${veilGateIndex} self:${veilSelfInspectIndex} memory:${veilMemoryIndex} model:${veilModelIndex}`,
    ],
  );
}

function extractDocumentedApiPaths(readme: string): string[] {
  const apiPaths = new Set<string>();
  const pathMatches = readme.match(/\/api\/[A-Za-z0-9:_/-]+/g) || [];
  for (const rawPath of pathMatches) {
    const normalized = rawPath.split("?")[0]?.trim() || rawPath;
    if (normalized.startsWith("/api/")) {
      apiPaths.add(normalized);
    }
  }
  return Array.from(apiPaths).sort((a, b) => a.localeCompare(b));
}

function extractImplementedRoutePaths(routesSource: string): Set<string> {
  const routePaths = new Set<string>();
  const routeRegex = /app\.(?:get|post|put|patch|delete)\(\s*["'`]([^"'`]+)["'`]/g;
  let match: RegExpExecArray | null = null;
  while ((match = routeRegex.exec(routesSource)) !== null) {
    const value = (match[1] || "").trim();
    if (!value.startsWith("/api/")) continue;
    routePaths.add(value);
  }
  return routePaths;
}

async function checkDocumentedApiPathsResolve(rootDir: string): Promise<SelfEvaluationCheck> {
  const [readme, routesSource] = await Promise.all([
    readWorkspaceFile(rootDir, "README.machine.md"),
    readWorkspaceFile(rootDir, "server/routes.ts"),
  ]);
  const documented = extractDocumentedApiPaths(readme);
  const implemented = extractImplementedRoutePaths(routesSource);
  const missing = documented.filter((pathValue) => !implemented.has(pathValue));

  return buildCheck(
    "documentation-symbol-resolution",
    "Rule",
    missing.length === 0,
    "README machine API symbols resolve to implemented routes.",
    [
      `documented.count=${documented.length}`,
      `implemented.count=${implemented.size}`,
      `missing=${missing.join(",") || "(none)"}`,
    ],
  );
}

async function checkInspectionModulesReadOnly(rootDir: string): Promise<SelfEvaluationCheck> {
  const inspectionFiles = ["server/self-inspection.ts", "server/self-inspection-command.ts"];
  const mutationTokenRegex = /\b(writeFile|appendFile|mkdir|rm|rename|unlink|copyFile|createWriteStream)\b/;
  const flagged: string[] = [];

  for (const relativePath of inspectionFiles) {
    const source = await readWorkspaceFile(rootDir, relativePath);
    if (mutationTokenRegex.test(source)) {
      flagged.push(relativePath);
    }
  }

  return buildCheck(
    "inspection-modules-read-only",
    "Contract",
    flagged.length === 0,
    "Self-inspection modules contain no direct write/mutation filesystem operations.",
    [
      `inspection.files=${inspectionFiles.join(",")}`,
      `flagged=${flagged.join(",") || "(none)"}`,
    ],
  );
}

function parseStatusForPath(statusText: string, relativePath: string): string | undefined {
  const normalizedTarget = normalizeWorkspacePath(relativePath).trim();
  const lines = statusText.split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    if (trimmed.endsWith(normalizedTarget)) {
      return trimmed;
    }
  }
  return undefined;
}

function resolveHashBaselineFile(observedPath: string): string | undefined {
  const normalized = normalizeWorkspacePath(observedPath);
  if (normalized === "server/veil-channel.mirror.ts") return "veil-channel.mirror.hash.txt";
  if (normalized.startsWith("proposals/pending/")) return "pending-proposal.hash.txt";
  return undefined;
}

function computeGitHash(rootDir: string, relativePath: string): string | undefined {
  try {
    const value = execFileSync("git", ["hash-object", relativePath], {
      cwd: rootDir,
      stdio: ["ignore", "pipe", "ignore"],
      encoding: "utf8",
    }).trim();
    return value || undefined;
  } catch {
    return undefined;
  }
}

async function checkObservedNotAuthoredImmutability(rootDir: string): Promise<SelfEvaluationCheck> {
  const snapshotRoot = path.join(rootDir, ".local", "continuity-snapshots");
  let snapshotDirs: string[] = [];
  try {
    const entries = await readdir(snapshotRoot, { withFileTypes: true, encoding: "utf8" });
    snapshotDirs = entries.filter((entry) => entry.isDirectory()).map((entry) => entry.name);
  } catch {
    return buildCheck(
      "observed-not-authored-immutable",
      "Contract",
      false,
      "Observed-not-authored immutability cannot be verified because no continuity snapshot exists.",
      [`snapshot.root=${normalizeWorkspacePath(snapshotRoot)}`],
    );
  }

  if (snapshotDirs.length === 0) {
    return buildCheck(
      "observed-not-authored-immutable",
      "Contract",
      false,
      "Observed-not-authored immutability cannot be verified because no continuity snapshot directories were found.",
      [`snapshot.root=${normalizeWorkspacePath(snapshotRoot)}`],
    );
  }

  snapshotDirs.sort((a, b) => b.localeCompare(a));
  const latestSnapshot = snapshotDirs[0];
  const snapshotDirPath = path.join(snapshotRoot, latestSnapshot);
  const observedListPath = path.join(snapshotDirPath, "observed-not-authored.txt");
  const statusPath = path.join(snapshotDirPath, "status.txt");

  let observedListText = "";
  let statusText = "";
  try {
    [observedListText, statusText] = await Promise.all([
      readFile(observedListPath, "utf8"),
      readFile(statusPath, "utf8"),
    ]);
  } catch {
    return buildCheck(
      "observed-not-authored-immutable",
      "Contract",
      false,
      "Observed-not-authored immutability cannot be verified because snapshot metadata files are missing.",
      [`snapshot.dir=${normalizeWorkspacePath(snapshotDirPath)}`],
    );
  }

  const observedPaths = observedListText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((value) => normalizeWorkspacePath(value));
  const changedPaths: string[] = [];
  const evidence: string[] = [`snapshot.dir=.local/continuity-snapshots/${latestSnapshot}`];

  for (const observedPath of observedPaths) {
    const baselineName = resolveHashBaselineFile(observedPath);
    if (baselineName) {
      const baselinePath = path.join(snapshotDirPath, baselineName);
      try {
        const baselineHash = (await readFile(baselinePath, "utf8")).trim();
        const currentHash = computeGitHash(rootDir, observedPath);
        if (!currentHash || currentHash !== baselineHash) {
          changedPaths.push(observedPath);
          evidence.push(
            `${observedPath}: baselineHash=${baselineHash || "missing"} currentHash=${currentHash || "missing"}`,
          );
        }
        continue;
      } catch {
        // fall through to status-based check
      }
    }

    const baselineStatus = parseStatusForPath(statusText, observedPath);
    const currentStatus = parseStatusForPath(
      execFileSync("git", ["status", "--porcelain=v1"], {
        cwd: rootDir,
        stdio: ["ignore", "pipe", "ignore"],
        encoding: "utf8",
      }),
      observedPath,
    );
    if ((baselineStatus || "") !== (currentStatus || "")) {
      changedPaths.push(observedPath);
      evidence.push(
        `${observedPath}: baselineStatus=${baselineStatus || "(none)"} currentStatus=${currentStatus || "(none)"}`,
      );
    }
  }

  if (changedPaths.length === 0) {
    evidence.push("changed=(none)");
  }

  return buildCheck(
    "observed-not-authored-immutable",
    "Contract",
    changedPaths.length === 0,
    "Observed-not-authored files remain unchanged from the latest continuity snapshot.",
    evidence,
  );
}

function selectChecksForProfile(
  profile: SelfEvaluationProfile,
  checks: Record<string, () => Promise<SelfEvaluationCheck>>,
): Array<() => Promise<SelfEvaluationCheck>> {
  if (profile === "gates") {
    return [checks.sharedDispatcher, checks.gatePrecedence];
  }
  if (profile === "contracts") {
    return [checks.readOnlyModules, checks.gatePrecedence, checks.observedNotAuthored];
  }
  if (profile === "all") {
    return [
      checks.sharedDispatcher,
      checks.noShadowDispatchers,
      checks.gatePrecedence,
      checks.docsResolve,
      checks.readOnlyModules,
      checks.observedNotAuthored,
    ];
  }
  return [
    checks.sharedDispatcher,
    checks.noShadowDispatchers,
    checks.docsResolve,
    checks.readOnlyModules,
  ];
}

export function isSelfEvaluationProfile(value: string): value is SelfEvaluationProfile {
  return PROFILE_SET.has(value as SelfEvaluationProfile);
}

export async function runSelfEvaluation(
  profile: SelfEvaluationProfile = "integrity",
  rootDir = process.cwd(),
): Promise<SelfEvaluationReport> {
  const index = await getSelfInspectionIndex({ rootDir });
  const activeVeilModulePath = await resolveActiveVeilModulePath(rootDir);
  const checks = {
    sharedDispatcher: () => checkSharedSelfInspectDispatcher(rootDir, activeVeilModulePath),
    noShadowDispatchers: () =>
      checkNoShadowSelfInspectExecutors(rootDir, activeVeilModulePath),
    gatePrecedence: () => checkSelfInspectGatePrecedence(rootDir, activeVeilModulePath),
    docsResolve: () => checkDocumentedApiPathsResolve(rootDir),
    readOnlyModules: () => checkInspectionModulesReadOnly(rootDir),
    observedNotAuthored: () => checkObservedNotAuthoredImmutability(rootDir),
  };
  const selectedChecks = selectChecksForProfile(profile, checks);
  const checkResults: SelfEvaluationCheck[] = [];

  for (const check of selectedChecks) {
    checkResults.push(await check());
  }

  const passed = checkResults.filter((entry) => entry.pass).length;
  const failed = checkResults.length - passed;
  return {
    profile,
    generatedAt: new Date().toISOString(),
    gitCommit: index.gitCommit,
    summary: {
      total: checkResults.length,
      passed,
      failed,
    },
    checks: checkResults,
  };
}

export function formatSelfEvaluationReport(report: SelfEvaluationReport): string {
  const lines = [
    `Evaluation: self-inspection ${report.profile}`,
    `Checks: ${report.summary.total}`,
    `Pass: ${report.summary.passed}`,
    `Fail: ${report.summary.failed}`,
  ];
  for (const check of report.checks) {
    lines.push(`${check.pass ? "[PASS]" : "[FAIL]"} ${check.id} (${check.class})`);
    lines.push(`  ${check.detail}`);
    for (const item of check.evidence) {
      lines.push(`  - ${item}`);
    }
  }
  return lines.join("\n");
}
