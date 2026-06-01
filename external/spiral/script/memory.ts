import { storage } from "../server/storage";
import {
  evaluateMemories,
  getMemoryPolicy,
  isCodeMemory,
  parsePositiveNumber,
  selectRelevantMemories,
  tokenizeForMemoryScoring,
  type MemoryEvaluation,
} from "../server/memory-scoring";
import {
  getMemoryRotationPolicy,
  type MemoryRotationAction,
  type MemoryRotationClusterReport,
  type MemoryRotationResult,
} from "../server/memory-rotation";
import {
  appendRotationTelemetryRecord,
  buildAdaptiveRecommendation,
  buildRotationTelemetryRecord,
  evolveAdaptiveState,
  readMemoryRotationAdaptiveState,
  readRotationTelemetryRecords,
  resolveEffectiveRotationPolicy,
  simulateAdaptiveReplay,
  summarizeRotationTelemetry,
  writeMemoryRotationAdaptiveState,
} from "../server/memory-rotation-adaptive";
import {
  computeRotationShadowTelemetry,
  summarizeRotationShadowTelemetry,
  type RotationShadowPairSample,
} from "../server/memory-rotation-shadow";
import { createHash } from "crypto";
import { appendFile, mkdir, readFile, readdir, stat, writeFile } from "fs/promises";
import path from "path";

const DEFAULT_PRUNE_MIN_SCORE = parsePositiveNumber(process.env.MEMORY_PRUNE_MIN_SCORE, 0.05);
const DEFAULT_PURGE_SOURCES = ["import", "import-summary", "system-summary"];
const DEFAULT_SCAN_MAX_FILES = 500;
const DEFAULT_SCAN_MAX_ITEMS = 240;
const DEFAULT_ROTATE_OUTPUT_LIMIT = 20;
const DEFAULT_DEMOTE_ANCHORS_COUNT = 10;
const DEFAULT_DEMOTE_KEEP_LATEST = 1;
const CODE_MEMORY_PREFIX = "Codebase:";
const CODE_SCAN_EXTENSIONS = new Set([".ts", ".tsx", ".js", ".jsx", ".json"]);
const CODE_SCAN_IGNORED_DIRS = new Set([
  ".git",
  ".local",
  "node_modules",
  "dist",
  "build",
  "coverage",
  ".next",
  ".cache",
  "attached_assets",
]);
const CODE_SCAN_IGNORED_FILES = new Set([
  "package-lock.json",
  "pnpm-lock.yaml",
  "yarn.lock",
]);
const MAX_FILE_BYTES = 220_000;
const MEMORY_GOVERNANCE_EVENTS_PATH = path.join(
  process.cwd(),
  ".local",
  "memory-governance-events.jsonl",
);
const MEMORY_GOVERNANCE_EVENT_SCHEMA_VERSION = "memory-governance-events.v1";
const NON_ANCHOR_TYPES = new Set([
  "fact",
  "preference",
  "observation",
  "interpretation",
  "narrative",
  "transient",
] as const);
const ANCHOR_PROTECTED_POLICY_PATTERN =
  /\b(always|never|must|must not|required|forbidden|do not|don't|policy|safety|constraint)\b/i;
const ANCHOR_PROTECTED_SECRET_PATTERN =
  /\b(api key|token|password|secret|credential|private key)\b/i;

function getFlag(args: string[], flag: string): boolean {
  return args.includes(flag);
}

function getOptionValue(args: string[], option: string): string | undefined {
  const prefix = `${option}=`;
  const inline = args.find((arg) => arg.startsWith(prefix));
  if (inline) {
    return inline.slice(prefix.length);
  }

  const index = args.indexOf(option);
  if (index >= 0 && index + 1 < args.length) {
    return args[index + 1];
  }

  return undefined;
}

function formatNumber(value: number, decimals = 3): string {
  return value.toFixed(decimals);
}

function buildReason(item: MemoryEvaluation): string {
  const reasons: string[] = [];
  reasons.push(`category=${item.category}`);
  reasons.push(`rawScore=${item.rawScore.toFixed(3)}`);
  reasons.push(`normalized=${item.normalizedScore.toFixed(3)}`);
  reasons.push(`age=${item.ageDays.toFixed(1)}d`);
  reasons.push(`halfLife=${item.halfLifeDays.toFixed(1)}d`);
  reasons.push(`effectiveWeight=${item.effectiveWeight.toFixed(3)}`);
  reasons.push(`decay=${item.decayMultiplier.toFixed(3)}`);
  reasons.push(`entropyPressure=${item.entropyPressure.toFixed(3)}`);
  reasons.push(`recency=${item.recencyMultiplier.toFixed(3)}`);
  reasons.push(`recurrence=${item.recurrenceBoost.toFixed(3)}`);
  reasons.push(`driftPenalty=${item.driftPenalty.toFixed(3)}`);
  reasons.push(`fossilPenalty=${item.fossilPenalty.toFixed(3)}`);
  reasons.push(`intentPenalty=${item.intentPenalty.toFixed(3)}`);
  reasons.push(`confirmationPenalty=${item.confirmationPenalty.toFixed(3)}`);

  if (item.hasContextTokens) {
    reasons.push(`overlap=${item.overlap}`);
    reasons.push(`overlapRatio=${item.overlapRatio.toFixed(3)}`);
  }

  if (!item.statusEligible) {
    reasons.push("status=blocked");
  }
  if (!item.domainEligible) {
    reasons.push("domain=blocked");
  }
  if (item.belowWeightThreshold) {
    reasons.push("belowWeightThreshold=true");
  }
  if (item.expired) {
    reasons.push("expired=true");
  }

  return reasons.join(", ");
}

function sortEvaluations(items: MemoryEvaluation[]): MemoryEvaluation[] {
  return [...items].sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    if (b.memory.lastConfirmedAt !== a.memory.lastConfirmedAt) {
      return b.memory.lastConfirmedAt - a.memory.lastConfirmedAt;
    }
    return b.memory.updatedAt - a.memory.updatedAt;
  });
}

function normalizeLine(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function toCodeMemory(value: string, sigilTag?: string): string {
  const normalizedValue = normalizeLine(value);
  if (!sigilTag) {
    return `${CODE_MEMORY_PREFIX} ${normalizedValue}`;
  }

  return `${CODE_MEMORY_PREFIX} [${normalizeLine(sigilTag)}] ${normalizedValue}`;
}

function parsePositiveInt(value: string | undefined, fallback: number): number {
  const parsed = Number.parseInt(value || "", 10);
  if (Number.isFinite(parsed) && parsed > 0) {
    return parsed;
  }
  return fallback;
}

function parseRatio(value: string | undefined, fallback: number): number {
  const parsed = Number.parseFloat(value || "");
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(0.95, Math.max(0.05, parsed));
}

function targetHalfLifeDays(type: string): number {
  switch (type) {
    case "fact":
      return 365;
    case "preference":
      return 180;
    case "observation":
      return 45;
    case "interpretation":
      return 30;
    case "narrative":
      return 90;
    case "transient":
      return 10;
    default:
      return 45;
  }
}

function parseDemotionType(value: string | undefined): "fact" | "preference" | "observation" | "interpretation" | "narrative" | "transient" {
  const normalized = (value || "").trim().toLowerCase();
  if (NON_ANCHOR_TYPES.has(normalized as never)) {
    return normalized as "fact" | "preference" | "observation" | "interpretation" | "narrative" | "transient";
  }
  return "observation";
}

function summarizeAnchorGovernance(memories: Array<{
  principalId?: string;
  memoryType: string;
  status: string;
}>, principalId = ""): {
  total: number;
  anchors: number;
  ratio: number;
  maxCount: number;
  maxRatio: number;
  exceeded: boolean;
} {
  const maxRatio = parseRatio(process.env.MEMORY_MAX_ANCHOR_RATIO, 0.4);
  const scoped = memories.filter((memory) => {
    if ((memory.status || "") === "released") return false;
    if (principalId && (memory.principalId || "") !== principalId) return false;
    return true;
  });
  const total = scoped.length;
  const anchors = scoped.filter((memory) => memory.memoryType === "anchor").length;
  const ratio = total > 0 ? anchors / total : 0;
  const maxCount = Math.max(1, Math.floor(total * maxRatio));
  return {
    total,
    anchors,
    ratio,
    maxCount,
    maxRatio,
    exceeded: anchors > maxCount,
  };
}

function stableStringify(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
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

function anchorProtectionReasons(
  memory: { id: string; content: string; source: string },
  latestProtectedIds: Set<string>,
): string[] {
  const reasons: string[] = [];
  if (latestProtectedIds.has(memory.id)) {
    reasons.push("KEEP_LATEST");
  }
  const source = normalizeSource(memory.source);
  if (source === "system-summary") {
    reasons.push("SOURCE_SYSTEM_SUMMARY");
  }
  if (ANCHOR_PROTECTED_POLICY_PATTERN.test(memory.content)) {
    reasons.push("POLICY_LEXEME");
  }
  if (ANCHOR_PROTECTED_SECRET_PATTERN.test(memory.content)) {
    reasons.push("SECRET_SIGNAL");
  }
  return reasons;
}

async function appendMemoryGovernanceEvent(event: unknown): Promise<void> {
  await mkdir(path.dirname(MEMORY_GOVERNANCE_EVENTS_PATH), { recursive: true });
  await appendFile(MEMORY_GOVERNANCE_EVENTS_PATH, `${stableStringify(event)}\n`, "utf8");
}

function sortIds(values: string[]): string[] {
  return [...values].sort((a, b) => a.localeCompare(b));
}

function setTokenSimilarity(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 || b.size === 0) return 0;
  let overlap = 0;
  for (const token of Array.from(a)) {
    if (b.has(token)) overlap++;
  }
  if (overlap === 0) return 0;

  const union = new Set([...Array.from(a), ...Array.from(b)]).size;
  const jaccard = union > 0 ? overlap / union : 0;
  const minSize = Math.min(a.size, b.size);
  const containment = minSize > 0 ? overlap / minSize : 0;
  return Math.max(jaccard, containment * 0.92);
}

function buildRotationRunId(
  memoryIds: string[],
  thresholds: ReturnType<typeof getMemoryRotationPolicy>,
): string {
  return createHash("sha1")
    .update(sortIds(memoryIds).join("|"))
    .update("::")
    .update(JSON.stringify(thresholds))
    .digest("hex")
    .slice(0, 16);
}

function rotationActionSummary(action: MemoryRotationAction): string {
  const from = Array.isArray(action.from) ? action.from.join(",") : action.from;
  switch (action.type) {
    case "merge":
      return `${action.reason} from=${from || "-"} -> ${action.to || "-"}`;
    case "rotate":
    case "hysteresis-hold":
      return `${action.reason} ${from || "-"} -> ${action.to || "-"}`;
    case "promote":
    case "demote":
    case "guard-block":
      return `${action.reason} id=${action.memoryId || "-"}`;
    case "merge-representative":
      return `${action.reason} rep=${action.to || "-"}`;
  }
}

function clusterImpactScore(cluster: MemoryRotationClusterReport): number {
  let impact = cluster.actions.length * 10;
  impact += Math.abs(cluster.before.size - cluster.after.size) * 6;
  if ((cluster.before.representativeId || "") !== (cluster.after.representativeId || "")) {
    impact += 12;
  }
  impact += Math.max(0, cluster.before.activeIds.length - cluster.after.activeIds.length) * 3;
  return impact;
}

function buildRotationNoOpReasons(result: MemoryRotationResult): string[] {
  const reasons: string[] = [];
  if (result.stats.clusterCount === 0) {
    reasons.push("No eligible clusters (all memories were anchors/released or empty).");
  }
  if (result.stats.clusterCount > 0 && result.stats.changedClusterCount === 0) {
    reasons.push("No cluster crossed merge similarity or rotation hysteresis thresholds.");
  }
  if (result.stats.quietGuardBlockedCount > 0) {
    reasons.push(`Guard blocks prevented ${result.stats.quietGuardBlockedCount} stale quiet reactivations.`);
  }
  return reasons;
}

function buildRepresentativeDiff(clusters: MemoryRotationClusterReport[]): {
  before: string[];
  after: string[];
  removed: string[];
  added: string[];
} {
  const before = sortIds(
    Array.from(
      new Set(
        clusters
          .map((cluster) => cluster.before.representativeId || "")
          .filter(Boolean),
      ),
    ),
  );
  const after = sortIds(
    Array.from(
      new Set(
        clusters
          .map((cluster) => cluster.after.representativeId || "")
          .filter(Boolean),
      ),
    ),
  );
  const beforeSet = new Set(before);
  const afterSet = new Set(after);
  return {
    before,
    after,
    removed: before.filter((id) => !afterSet.has(id)),
    added: after.filter((id) => !beforeSet.has(id)),
  };
}

function formatAdaptiveDelta(delta: {
  key: string;
  from: number;
  to: number;
  delta: number;
  reason: string;
  detail: string;
}): string {
  const sign = delta.delta > 0 ? "+" : "";
  return `${delta.key}: ${delta.from} -> ${delta.to} (${sign}${delta.delta}) reason=${delta.reason} detail=${delta.detail}`;
}

function printAdaptiveLayer(
  label: string,
  layer: {
    canApply: boolean;
    blockedReasons: string[];
    deltas: Array<{
      key: string;
      from: number;
      to: number;
      delta: number;
      reason: string;
      detail: string;
    }>;
  },
): void {
  console.log(`${label}: ${layer.canApply ? "ready" : "blocked"} deltas=${layer.deltas.length}`);
  if (layer.deltas.length > 0) {
    for (const delta of layer.deltas) {
      console.log(`- ${formatAdaptiveDelta(delta)}`);
    }
  }
  if (layer.blockedReasons.length > 0) {
    for (const reason of layer.blockedReasons) {
      console.log(`- blocked: ${reason}`);
    }
  }
}

function printShadowSample(samples: RotationShadowPairSample[]): void {
  if (samples.length === 0) {
    console.log("Semantic sample: no pairwise samples available.");
    return;
  }
  console.log(`Semantic sample: showing ${samples.length} pair(s)`);
  samples.forEach((sample, index) => {
    console.log(
      `${index + 1}. cluster=${sample.clusterId} a=${sample.aId} b=${sample.bId} lex=${sample.lexicalSimilarity.toFixed(3)} sem=${sample.semanticSimilarity.toFixed(3)} disagree=${sample.disagreement.toFixed(3)} bucket=${sample.bucket}`,
    );
    console.log(`   a: ${sample.aContent}`);
    console.log(`   b: ${sample.bContent}`);
  });
}

function summarizeReplay(records: Awaited<ReturnType<typeof readRotationTelemetryRecords>>, policy: ReturnType<typeof getMemoryRotationPolicy>): {
  bounded: boolean;
  steps: number;
  mergeSimilarityRange: number;
  rotationHysteresisRange: number;
  maxActivePerGroupRange: number;
} {
  return simulateAdaptiveReplay({
    basePolicy: policy,
    records,
  });
}

function parseCsvList(value: string | undefined): string[] {
  if (!value) return [];
  return value
    .split(",")
    .map((token) => token.trim())
    .filter(Boolean);
}

function normalizeSource(value: string | undefined): string {
  return (value || "").trim().toLowerCase();
}

function sourceMatchesPattern(source: string, pattern: string): boolean {
  const normalizedSource = normalizeSource(source);
  const normalizedPattern = normalizeSource(pattern);
  if (!normalizedSource || !normalizedPattern) return false;
  if (normalizedPattern.endsWith("*")) {
    const prefix = normalizedPattern.slice(0, -1);
    if (!prefix) return false;
    return normalizedSource.startsWith(prefix);
  }
  return normalizedSource === normalizedPattern;
}

function toWorkspaceRelative(filePath: string): string {
  const relative = path.relative(process.cwd(), filePath);
  return relative.split(path.sep).join("/");
}

async function collectCodeFiles(rootDir: string, maxFiles: number): Promise<string[]> {
  const files: string[] = [];

  async function walk(currentDir: string): Promise<void> {
    if (files.length >= maxFiles) return;
    const entries = await readdir(currentDir, { withFileTypes: true });

    for (const entry of entries) {
      if (files.length >= maxFiles) return;

      const fullPath = path.join(currentDir, entry.name);
      if (entry.isDirectory()) {
        if (CODE_SCAN_IGNORED_DIRS.has(entry.name)) {
          continue;
        }
        await walk(fullPath);
        continue;
      }

      if (!entry.isFile()) continue;
      if (CODE_SCAN_IGNORED_FILES.has(entry.name)) continue;

      const ext = path.extname(entry.name).toLowerCase();
      if (!CODE_SCAN_EXTENSIONS.has(ext)) continue;
      files.push(fullPath);
    }
  }

  await walk(rootDir);
  return files;
}

function extractRouteSummaries(source: string): string[] {
  const routeRegex = /app\.(get|post|put|patch|delete)\(\s*["'`]([^"'`]+)["'`]/g;
  const routes = new Set<string>();
  let match: RegExpExecArray | null;
  while ((match = routeRegex.exec(source)) !== null) {
    routes.add(`${match[1].toUpperCase()} ${match[2]}`);
  }
  return Array.from(routes);
}

function extractExports(source: string): string[] {
  const exports = new Set<string>();
  const namedExportRegex = /\bexport\s+(?:async\s+)?(?:function|const|class|type|interface|enum)\s+([A-Za-z0-9_]+)/g;
  const groupExportRegex = /\bexport\s*\{([^}]+)\}/g;

  let match: RegExpExecArray | null;
  while ((match = namedExportRegex.exec(source)) !== null) {
    exports.add(match[1]);
  }

  while ((match = groupExportRegex.exec(source)) !== null) {
    const parts = match[1]
      .split(",")
      .map((value) => value.trim().split(/\s+as\s+/i)[0])
      .filter(Boolean);
    for (const part of parts) {
      exports.add(part);
    }
  }

  return Array.from(exports);
}

async function buildCodeMemories(
  maxFiles: number,
  maxItems: number,
  sigilTag?: string,
): Promise<string[]> {
  const candidateMemories = new Set<string>();

  try {
    const packageText = await readFile(path.join(process.cwd(), "package.json"), "utf8");
    const pkg = JSON.parse(packageText) as {
      scripts?: Record<string, string>;
      dependencies?: Record<string, string>;
      devDependencies?: Record<string, string>;
    };

    const scripts = Object.keys(pkg.scripts || {});
    if (scripts.length > 0) {
      candidateMemories.add(
        toCodeMemory(`Project npm scripts include ${scripts.slice(0, 10).join(", ")}.`, sigilTag),
      );
    }

    const dependencyNames = Object.keys(pkg.dependencies || {});
    const coreDeps = dependencyNames
      .filter((name) =>
        ["react", "express", "drizzle-orm", "zod", "wouter", "next-themes", "@tanstack/react-query"].includes(name),
      )
      .slice(0, 8);
    if (coreDeps.length > 0) {
      candidateMemories.add(
        toCodeMemory(`Primary dependencies include ${coreDeps.join(", ")}.`, sigilTag),
      );
    }
  } catch {
    // ignore package metadata parse errors in scan mode
  }

  const files = await collectCodeFiles(process.cwd(), maxFiles);
  for (const filePath of files) {
    if (candidateMemories.size >= maxItems) break;

    let source = "";
    try {
      const fileStat = await stat(filePath);
      if (fileStat.size > MAX_FILE_BYTES) continue;
      source = await readFile(filePath, "utf8");
    } catch {
      continue;
    }

    const relativePath = toWorkspaceRelative(filePath);
    const exports = extractExports(source);
    if (exports.length > 0) {
      candidateMemories.add(
        toCodeMemory(
          `File ${relativePath} exports ${exports.slice(0, 6).join(", ")}.`,
          sigilTag,
        ),
      );
    }

    if (relativePath === "server/routes.ts" || relativePath.endsWith("/routes.ts")) {
      const routes = extractRouteSummaries(source);
      if (routes.length > 0) {
        candidateMemories.add(
          toCodeMemory(
            `API routes include ${routes.slice(0, 10).join("; ")}.`,
            sigilTag,
          ),
        );
      }
    }
  }

  return Array.from(candidateMemories).slice(0, maxItems);
}

async function runScanCode(args: string[]): Promise<void> {
  const maxFiles = parsePositiveInt(getOptionValue(args, "--max-files"), DEFAULT_SCAN_MAX_FILES);
  const maxItems = parsePositiveInt(getOptionValue(args, "--max-items"), DEFAULT_SCAN_MAX_ITEMS);
  const dryRun = getFlag(args, "--dry-run");
  const invoked = getFlag(args, "--invoked");
  const keepExisting = getFlag(args, "--keep-existing");
  const sigilTag = getOptionValue(args, "--sigil");

  const existingMemories = await storage.getMemories();
  const existingCodeMemories = existingMemories.filter((memory) => isCodeMemory(memory.content));
  const generatedMemories = await buildCodeMemories(maxFiles, maxItems, sigilTag);
  const effectiveDryRun = dryRun || !invoked;

  if (effectiveDryRun) {
    console.log(
      `Code scan (dry-run): existingCode=${existingCodeMemories.length} generated=${generatedMemories.length} maxFiles=${maxFiles} maxItems=${maxItems} invoked=${invoked ? "yes" : "no"}${sigilTag ? ` sigil=${normalizeLine(sigilTag)}` : ""}`,
    );
    if (!invoked) {
      console.log("Write is blocked without explicit invocation. Re-run with --invoked to apply.");
    }
    for (const memory of generatedMemories.slice(0, 30)) {
      console.log(`- ${memory}`);
    }
    return;
  }

  let deleted = 0;
  if (!keepExisting) {
    for (const memory of existingCodeMemories) {
      const ok = await storage.deleteMemory(memory.id);
      if (ok) deleted++;
    }
  }

  let upserted = 0;
  for (const content of generatedMemories) {
    const memory = await storage.upsertMemory(content);
    if (memory) upserted++;
  }

  console.log(
    `Code scan complete: released=${deleted} upserted=${upserted} keepExisting=${keepExisting ? "yes" : "no"}`,
  );
}

async function runReview(args: string[]): Promise<void> {
  const context = getOptionValue(args, "--context") ?? "";
  const includeExpired = getFlag(args, "--all");
  const asJson = getFlag(args, "--json");
  const limitArg = getOptionValue(args, "--limit");
  const limit = Math.max(
    1,
    Number.parseInt(limitArg || "100", 10) || 100,
  );

  const allMemories = await storage.getMemories();
  const policy = getMemoryPolicy();
  const evaluated = sortEvaluations(evaluateMemories(allMemories, context, policy));
  const selectedIds = new Set(selectRelevantMemories(allMemories, context, 8, policy).map((m) => m.id));
  const visible = (includeExpired ? evaluated : evaluated.filter((item) => !item.expired)).slice(0, limit);
  const governance = summarizeAnchorGovernance(allMemories);

  if (asJson) {
    const payload = visible.map((item) => ({
      id: item.memory.id,
      content: item.memory.content,
      score: item.score,
      category: item.category,
      expired: item.expired,
      selectedForPrompt: selectedIds.has(item.memory.id),
      reason: buildReason(item),
    }));
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  console.log(
    `Memory review: total=${allMemories.length} visible=${visible.length} selected=${selectedIds.size} contextTokens=${context.trim() ? "on" : "off"}`,
  );
  console.log(
    `Anchor governance: anchors=${governance.anchors}/${governance.total} ratio=${governance.ratio.toFixed(3)} cap=${governance.maxCount} limit=${governance.maxRatio.toFixed(3)} status=${governance.exceeded ? "exceeded" : "ok"}`,
  );
  if (governance.exceeded) {
    console.log(
      "Anchor governance warning: new anchors are blocked unless explicitly forced. Use `memory:demote-anchors` to recover eligible orbit memories.",
    );
  }
  if (visible.length === 0) {
    console.log("No memories to display.");
    return;
  }

  visible.forEach((item, index) => {
    const marker = selectedIds.has(item.memory.id) ? "*" : " ";
    console.log(
      `${marker} ${index + 1}. score=${formatNumber(item.score)} category=${item.category} id=${item.memory.id}`,
    );
    console.log(`   reason: ${buildReason(item)}`);
    console.log(`   content: ${item.memory.content}`);
  });
}

async function runPrune(args: string[]): Promise<void> {
  const context = getOptionValue(args, "--context") ?? "";
  const minScoreArg = getOptionValue(args, "--min-score");
  const minScore = parsePositiveNumber(minScoreArg, DEFAULT_PRUNE_MIN_SCORE);
  const dryRun = getFlag(args, "--dry-run");
  const applyToAllCategories = getFlag(args, "--all-categories");

  const allMemories = await storage.getMemories();
  const policy = getMemoryPolicy();
  const evaluated = evaluateMemories(allMemories, context, policy);

  const toDelete = evaluated.filter((item) => {
    if (item.expired) return true;

    const lowScore = item.score < minScore;
    if (!lowScore) return false;

    return applyToAllCategories || item.category === "observation" || item.category === "transient";
  });

  if (toDelete.length === 0) {
    console.log("Prune complete: nothing to remove.");
    return;
  }

  console.log(
    `Prune candidates=${toDelete.length} (dryRun=${dryRun ? "yes" : "no"}, minScore=${minScore.toFixed(3)}, allCategories=${applyToAllCategories ? "yes" : "no"})`,
  );
  for (const item of sortEvaluations(toDelete)) {
    const reason = item.expired ? "expired" : `low-score(${item.score.toFixed(3)} < ${minScore.toFixed(3)})`;
    console.log(`- ${item.memory.id} [${item.category}] ${reason}: ${item.memory.content}`);
  }

  if (dryRun) {
    return;
  }

  let released = 0;
  for (const item of toDelete) {
    const ok = await storage.deleteMemory(item.memory.id);
    if (ok) released++;
  }

  console.log(`Prune complete: released=${released}`);
}

async function runRotate(args: string[]): Promise<void> {
  const apply = getFlag(args, "--apply");
  const dryRun = !apply;
  const asJson = getFlag(args, "--json");
  const outPath = getOptionValue(args, "--out");
  const limit = parsePositiveInt(getOptionValue(args, "--limit"), DEFAULT_ROTATE_OUTPUT_LIMIT);
  const clusterFilter = (getOptionValue(args, "--cluster") || "").trim();
  const memoryFilter = (getOptionValue(args, "--memory") || "").trim();
  const showThresholds = getFlag(args, "--thresholds");
  const showDiff = getFlag(args, "--diff");
  const showMetrics = getFlag(args, "--metrics");
  const semanticPreview = getFlag(args, "--semantic-preview");
  const semanticSample = getFlag(args, "--semantic-sample");
  const semanticSampleSize = parsePositiveInt(getOptionValue(args, "--sample-size"), 20);
  const computeEmbeddings = getFlag(args, "--compute-embeddings");
  const adaptivePreview = getFlag(args, "--adaptive-preview") || getFlag(args, "--adaptive-apply");
  const adaptiveApply = getFlag(args, "--adaptive-apply");
  const replayCheck = getFlag(args, "--replay-check");

  const beforeMemories = await storage.getMemories();
  const beforeMap = new Map(beforeMemories.map((memory) => [memory.id, memory]));
  const baseThresholds = getMemoryRotationPolicy();
  const adaptiveState = await readMemoryRotationAdaptiveState();
  const effectiveThresholds = resolveEffectiveRotationPolicy(baseThresholds, adaptiveState);
  const startedAt = Date.now();
  const governance = summarizeAnchorGovernance(beforeMemories);
  const result = await storage.rotateMemoryOrbit({
    apply,
    now: startedAt,
    policy: effectiveThresholds,
  });
  const elapsedMs = Date.now() - startedAt;
  const shadow = await computeRotationShadowTelemetry({
    memories: beforeMemories,
    result,
    includeSample: semanticSample,
    sampleSize: semanticSampleSize,
    persistCache: computeEmbeddings || apply,
    now: startedAt,
  });

  const telemetryHistory = await readRotationTelemetryRecords();
  let appendedTelemetry = null as Awaited<ReturnType<typeof appendRotationTelemetryRecord>> | null;
  if (apply) {
    const telemetryRecord = buildRotationTelemetryRecord({
      beforeMemories,
      durationMs: elapsedMs,
      history: telemetryHistory,
      policy: effectiveThresholds,
      result,
      shadow: shadow.telemetry,
      timestamp: startedAt,
    });
    appendedTelemetry = await appendRotationTelemetryRecord(telemetryRecord, {
      nowFn: () => Date.now(),
    });
  }
  const telemetryRecords = apply
    ? [...telemetryHistory, appendedTelemetry!].sort((a, b) => a.timestamp - b.timestamp)
    : telemetryHistory;
  const telemetrySummary = summarizeRotationTelemetry(telemetryRecords, startedAt);
  const shadowSummary = summarizeRotationShadowTelemetry(telemetryRecords, startedAt);
  const adaptiveRecommendation = buildAdaptiveRecommendation({
    basePolicy: baseThresholds,
    records: telemetryRecords,
    state: adaptiveState,
    now: startedAt,
  });
  const replay = replayCheck
    ? summarizeReplay(telemetryRecords, baseThresholds)
    : null;

  let adaptiveApplied = false;
  if (apply || adaptiveApply) {
    const evolution = evolveAdaptiveState({
      apply: adaptiveApply,
      recommendation: adaptiveRecommendation,
      runId:
        appendedTelemetry?.runId ||
        buildRotationRunId(beforeMemories.map((memory) => memory.id), effectiveThresholds),
      state: adaptiveState,
    });
    adaptiveApplied = evolution.applied;
    await writeMemoryRotationAdaptiveState(evolution.state);
  }

  const changedClusters = result.clusters.filter((cluster) => cluster.changed);
  let focusClusterId = clusterFilter;
  if (memoryFilter && !focusClusterId) {
    const found = result.clusters.find(
      (cluster) =>
        cluster.before.memberIds.includes(memoryFilter) || cluster.after.memberIds.includes(memoryFilter),
    );
    if (!found) {
      console.log(`Memory rotate: memory ${memoryFilter} was not found in any eligible cluster.`);
      return;
    }
    focusClusterId = found.clusterId;
  }

  const selectedClusters = (focusClusterId
    ? result.clusters.filter((cluster) => cluster.clusterId === focusClusterId)
    : changedClusters
  )
    .sort((a, b) => {
      const impactDiff = clusterImpactScore(b) - clusterImpactScore(a);
      if (impactDiff !== 0) return impactDiff;
      return a.clusterId.localeCompare(b.clusterId);
    });

  if (focusClusterId && selectedClusters.length === 0) {
    console.log(`Memory rotate: cluster ${focusClusterId} was not found.`);
    return;
  }

  const representativeDiff = buildRepresentativeDiff(result.clusters);
  const reportPayload = {
    runId:
      appendedTelemetry?.runId ||
      buildRotationRunId(beforeMemories.map((memory) => memory.id), effectiveThresholds),
    timestamp: Math.floor(startedAt / 1000),
    dryRun,
    stats: {
      ...result.stats,
      netDelta: result.stats.totalAfter - result.stats.totalBefore,
      elapsedMs,
      changedClusterCount: changedClusters.length,
    },
    thresholds: {
      base: baseThresholds,
      effective: effectiveThresholds,
      netAfterAdaptive: adaptiveRecommendation.net.policyAfter,
    },
    telemetry: {
      totalRuns: telemetrySummary.totalRuns,
      latestTimestamp: telemetrySummary.latestTimestamp,
      ewma: telemetrySummary.ewma,
      timeWindows: telemetrySummary.timeWindows,
      runWindows: telemetrySummary.runWindows,
      effectAlerts: telemetrySummary.effectAlerts,
      fieldAlerts: telemetrySummary.fieldAlerts,
      shadowCurrent: shadow.telemetry,
      shadowSummary,
      appendedRecord: appendedTelemetry,
    },
    semanticSample: shadow.sample,
    adaptive: {
      preview: adaptiveRecommendation,
      applied: adaptiveApplied,
    },
    replay,
    diff: representativeDiff,
    clusters: result.clusters,
  };

  if (outPath) {
    const resolved = path.resolve(process.cwd(), outPath);
    await writeFile(resolved, JSON.stringify(reportPayload, null, 2), "utf8");
  }

  if (asJson) {
    console.log(JSON.stringify(reportPayload, null, 2));
    return;
  }

  console.log(
    `Memory rotate (${dryRun ? "dry-run" : "apply"}): scanned=${result.stats.totalBefore} clusters=${result.stats.clusterCount} changed=${changedClusters.length} merged=${result.stats.mergedCount} rotated=${result.stats.rotatedCount} capDemotions=${result.stats.capacityDemotedCount} guardBlocks=${result.stats.quietGuardBlockedCount} netDelta=${result.stats.totalAfter - result.stats.totalBefore} elapsed=${elapsedMs}ms`,
  );
  if (governance.exceeded) {
    console.log(
      `Anchor governance warning: anchors=${governance.anchors}/${governance.total} ratio=${governance.ratio.toFixed(3)} exceeds cap=${governance.maxCount} @ limit=${governance.maxRatio.toFixed(3)}. New anchors require --force semantics and explicit pin.`,
    );
  }
  if (outPath) {
    console.log(`Report written: ${path.resolve(process.cwd(), outPath)}`);
  }

  if (showThresholds) {
    console.log(
      `Thresholds (effective): clusterSimilarity=${effectiveThresholds.clusterSimilarityThreshold.toFixed(2)} mergeSimilarity=${effectiveThresholds.mergeSimilarityThreshold.toFixed(2)} hysteresis=${effectiveThresholds.rotationHysteresis.toFixed(2)} activeSlots=${effectiveThresholds.activeSlotsPerCluster} maxActivePerGroup=${effectiveThresholds.maxActivePerGroup} reactivationWindowDays=${effectiveThresholds.reactivationWindowDays}`,
    );
  }

  if (showDiff) {
    console.log(
      `Representative diff: before=${representativeDiff.before.length} after=${representativeDiff.after.length} added=${representativeDiff.added.join(",") || "(none)"} removed=${representativeDiff.removed.join(",") || "(none)"}`,
    );
  }

  if (showMetrics) {
    console.log(
      `Metrics: runs=${telemetrySummary.totalRuns} ewma(change=${telemetrySummary.ewma.changeRate.toFixed(3)} merge=${telemetrySummary.ewma.mergeRate.toFixed(3)} churn=${telemetrySummary.ewma.representativeChurnRate.toFixed(3)} H_var=${telemetrySummary.ewma.H_var.toFixed(3)} H_top1=${telemetrySummary.ewma.H_top1_share.toFixed(3)} H_hhi=${telemetrySummary.ewma.H_hhi.toFixed(3)})`,
    );
    console.log(
      `Alerts(effect): churn=${telemetrySummary.effectAlerts.identity_churn_high ? "on" : "off"} merge=${telemetrySummary.effectAlerts.merge_saturation ? "on" : "off"} cap=${telemetrySummary.effectAlerts.cap_pressure_high ? "on" : "off"} stagnation=${telemetrySummary.effectAlerts.stability_stagnation ? "on" : "off"}`,
    );
    console.log(
      `Alerts(field): expanding=${telemetrySummary.fieldAlerts.entropy_field_expanding ? "on" : "off"} compressing=${telemetrySummary.fieldAlerts.entropy_field_compressing ? "on" : "off"} skew=${telemetrySummary.fieldAlerts.entropy_skew_dominant_cluster ? "on" : "off"}`,
    );
  }

  if (semanticPreview) {
    const stats = shadow.telemetry.semantic_stats;
    const bucket = shadow.telemetry.disagreement_buckets;
    console.log(
      `Semantic shadow: model=${shadow.telemetry.embeddingModel} lexicalMean=${stats.lexical_mean.toFixed(3)} semanticMean=${stats.semantic_mean.toFixed(3)} disagreementMean=${stats.mean_disagreement.toFixed(3)} disagreementRate=${stats.disagreement_rate.toFixed(3)}`,
    );
    console.log(
      `Semantic buckets: sem>lex=${bucket.SEMANTIC_STRONGER_THAN_LEXICAL} lex>sem=${bucket.LEXICAL_STRONGER_THAN_SEMANTIC} bothStrong=${bucket.BOTH_STRONG} bothWeak=${bucket.BOTH_WEAK} near=${bucket.NEAR_MATCH}`,
    );
    console.log(
      `Semantic windows: runs=${shadowSummary.totalRuns} ewma(disagreement=${shadowSummary.ewma.mean_disagreement.toFixed(3)} rate=${shadowSummary.ewma.disagreement_rate.toFixed(3)})`,
    );
    const topShadowClusters = [...shadow.telemetry.clusters]
      .sort((a, b) => {
        if (b.mean_disagreement !== a.mean_disagreement) return b.mean_disagreement - a.mean_disagreement;
        return a.clusterId.localeCompare(b.clusterId);
      })
      .slice(0, 5);
    if (topShadowClusters.length > 0) {
      console.log(`Semantic cluster disagreement (top ${topShadowClusters.length}):`);
      for (const cluster of topShadowClusters) {
        console.log(
          `- ${cluster.clusterId} lex=${cluster.lexical_mean.toFixed(3)} sem=${cluster.semantic_mean.toFixed(3)} disagree=${cluster.mean_disagreement.toFixed(3)} members=${cluster.members.length}`,
        );
      }
    }
  }

  if (semanticSample) {
    printShadowSample(shadow.sample);
  }

  if (adaptivePreview) {
    printAdaptiveLayer("Adaptive effect", adaptiveRecommendation.effect);
    printAdaptiveLayer("Adaptive field", adaptiveRecommendation.field);
    printAdaptiveLayer("Adaptive net", adaptiveRecommendation.net);
    if (adaptiveApply) {
      console.log(`Adaptive apply: ${adaptiveApplied ? "applied" : "no-op"}`);
    }
  }

  if (replay) {
    console.log(
      `Replay convergence: bounded=${replay.bounded ? "yes" : "no"} steps=${replay.steps} range(merge=${replay.mergeSimilarityRange.toFixed(4)} hysteresis=${replay.rotationHysteresisRange.toFixed(4)} cap=${replay.maxActivePerGroupRange.toFixed(2)})`,
    );
  }

  if (selectedClusters.length === 0) {
    console.log("No changed clusters.");
    const reasons = buildRotationNoOpReasons(result);
    if (reasons.length > 0) {
      console.log("No-op reasons:");
      for (const reason of reasons) {
        console.log(`- ${reason}`);
      }
    }
    return;
  }

  const visible = selectedClusters.slice(0, Math.max(1, limit));
  console.log(`Changed clusters: showing ${visible.length} of ${selectedClusters.length}`);
  visible.forEach((cluster, index) => {
    const repBefore = cluster.before.representativeId || "-";
    const repAfter = cluster.after.representativeId || "-";
    console.log(
      `${index + 1}. ${cluster.clusterId} group=${cluster.groupKey} members=${cluster.before.size}->${cluster.after.size} rep=${repBefore}->${repAfter}`,
    );
    console.log(
      `   features=${cluster.signals.topFeatures.join(",") || "(none)"} similarity=${cluster.signals.similarity.toFixed(3)} actions=${cluster.actions.length}`,
    );
    if (cluster.signals.hysteresis) {
      const signal = cluster.signals.hysteresis;
      console.log(
        `   hysteresis: challenger=${signal.challengerId || "-"}(${signal.challengerScore.toFixed(3)}) incumbent=${signal.incumbentId || "-"}(${signal.incumbentScore.toFixed(3)}) threshold=${signal.triggerThreshold.toFixed(3)} triggered=${signal.triggered ? "yes" : "no"}`,
      );
    }
    for (const action of cluster.actions) {
      const detail = action.detail ? ` (${action.detail})` : "";
      console.log(`   - ${rotationActionSummary(action)}${detail}`);
    }
  });

  if (memoryFilter) {
    const targetCluster = selectedClusters[0];
    const baseMemory =
      beforeMap.get(memoryFilter) ||
      result.memories.find((memory) => memory.id === memoryFilter);
    if (!baseMemory) {
      console.log(`Memory focus: ${memoryFilter} not present in post-rotation memory map.`);
      return;
    }
    const targetTokens = tokenizeForMemoryScoring(baseMemory.content);
    const afterMap = new Map(result.memories.map((memory) => [memory.id, memory]));
    const neighborIds = sortIds(
      Array.from(
        new Set([
          ...targetCluster.before.memberIds,
          ...targetCluster.after.memberIds,
        ]),
      ),
    ).filter((id) => id !== memoryFilter);
    const neighbors = neighborIds
      .map((id) => {
        const memory = beforeMap.get(id) || afterMap.get(id);
        if (!memory) return null;
        return {
          id,
          similarity: setTokenSimilarity(targetTokens, tokenizeForMemoryScoring(memory.content)),
        };
      })
      .filter((item): item is { id: string; similarity: number } => Boolean(item))
      .sort((a, b) => {
        if (b.similarity !== a.similarity) return b.similarity - a.similarity;
        return a.id.localeCompare(b.id);
      })
      .slice(0, 8);
    console.log(`Memory focus: id=${memoryFilter} cluster=${targetCluster.clusterId}`);
    for (const neighbor of neighbors) {
      console.log(`   neighbor=${neighbor.id} similarity=${neighbor.similarity.toFixed(3)}`);
    }
  }
}

async function runPurge(args: string[]): Promise<void> {
  const sourceArg = getOptionValue(args, "--source");
  const sourcePatterns = parseCsvList(sourceArg);
  const effectivePatterns = sourcePatterns.length > 0 ? sourcePatterns : DEFAULT_PURGE_SOURCES;
  const principalId = (getOptionValue(args, "--principal") || "").trim();
  const includeReleased = getFlag(args, "--include-released");
  const confirm = getFlag(args, "--confirm");
  const modeRaw = normalizeSource(getOptionValue(args, "--mode"));
  const mode: "release" | "delete" = modeRaw === "release" ? "release" : "delete";

  const allMemories = await storage.getMemories();
  const targets = allMemories.filter((memory) => {
    if (!includeReleased && memory.status === "released") return false;
    if (principalId && (memory.principalId || "") !== principalId) return false;
    return effectivePatterns.some((pattern) => sourceMatchesPattern(memory.source, pattern));
  });

  if (targets.length === 0) {
    console.log(
      `Purge complete: no matches (patterns=${effectivePatterns.join(", ")}${principalId ? ` principal=${principalId}` : ""}).`,
    );
    return;
  }

  const countsBySource = new Map<string, number>();
  for (const memory of targets) {
    const key = normalizeSource(memory.source) || "(empty)";
    countsBySource.set(key, (countsBySource.get(key) || 0) + 1);
  }
  const sourceSummary = Array.from(countsBySource.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([source, count]) => `${source}:${count}`)
    .join(", ");

  console.log(
    `Purge candidates=${targets.length} mode=${mode} patterns=${effectivePatterns.join(", ")} includeReleased=${includeReleased ? "yes" : "no"}${principalId ? ` principal=${principalId}` : ""}`,
  );
  console.log(`Sources: ${sourceSummary}`);
  for (const memory of targets.slice(0, 40)) {
    console.log(`- ${memory.id} [${memory.status}] source=${memory.source} content=${memory.content}`);
  }
  if (targets.length > 40) {
    console.log(`...and ${targets.length - 40} more`);
  }

  if (!confirm) {
    console.log("Dry-run only. Re-run with --confirm to apply purge.");
    return;
  }

  let affected = 0;
  for (const memory of targets) {
    const ok =
      mode === "delete"
        ? await storage.hardDeleteMemory(memory.id)
        : await storage.deleteMemory(memory.id);
    if (ok) affected++;
  }
  await storage.flushPersistence();
  console.log(`Purge complete: affected=${affected} mode=${mode}`);
}

async function runAdd(args: string[]): Promise<void> {
  const content = args.join(" ").trim();
  if (!content) {
    console.error('Usage: npm run memory:add -- "Your memory content"');
    process.exitCode = 1;
    return;
  }

  const memory = await storage.upsertMemory(content);
  if (!memory) {
    console.error("Failed to add memory.");
    process.exitCode = 1;
    return;
  }

  const [evaluation] = evaluateMemories([memory], "", getMemoryPolicy());
  console.log(`Memory saved: id=${memory.id}`);
  console.log(`Category: ${evaluation.category}`);
  console.log(`Content: ${memory.content}`);
}

async function runDemoteAnchors(args: string[]): Promise<void> {
  const apply = getFlag(args, "--apply");
  const dryRun = !apply;
  const principalId = (getOptionValue(args, "--principal") || "").trim();
  const count = parsePositiveInt(getOptionValue(args, "--count"), DEFAULT_DEMOTE_ANCHORS_COUNT);
  const ids = parseCsvList(getOptionValue(args, "--ids"));
  const allowCritical = getFlag(args, "--allow-critical") || getFlag(args, "--allow-protected");
  const keepLatest = parsePositiveInt(
    getOptionValue(args, "--keep-latest"),
    DEFAULT_DEMOTE_KEEP_LATEST,
  );
  const reasonRaw = (getOptionValue(args, "--reason") || "").trim();
  const reason = reasonRaw ? normalizeLine(reasonRaw) : "manual-quota-cleanup";
  const targetType = parseDemotionType(getOptionValue(args, "--to"));

  const allMemories = await storage.getMemories();
  const beforeGovernance = summarizeAnchorGovernance(allMemories, principalId);
  const anchors = allMemories
    .filter((memory) => memory.memoryType === "anchor")
    .filter((memory) => memory.status !== "released")
    .filter((memory) => !principalId || (memory.principalId || "") === principalId);

  const latestProtectedIds = new Set(
    [...anchors]
      .sort((a, b) => {
        if (b.lastConfirmedAt !== a.lastConfirmedAt) return b.lastConfirmedAt - a.lastConfirmedAt;
        if (b.updatedAt !== a.updatedAt) return b.updatedAt - a.updatedAt;
        return a.id.localeCompare(b.id);
      })
      .slice(0, Math.min(anchors.length, keepLatest))
      .map((memory) => memory.id),
  );

  const protectionById = new Map<string, string[]>();
  for (const memory of anchors) {
    const reasons = anchorProtectionReasons(memory, latestProtectedIds);
    if (reasons.length > 0) {
      protectionById.set(memory.id, reasons);
    }
  }

  const selected: typeof anchors = [];
  const skippedProtected: Array<{ id: string; reasons: string[] }> = [];
  const missingIds: string[] = [];
  if (ids.length > 0) {
    const idSet = new Set(ids);
    const foundIds = new Set<string>();
    for (const memory of anchors) {
      if (!idSet.has(memory.id)) continue;
      foundIds.add(memory.id);
      const reasons = protectionById.get(memory.id) || [];
      if (!allowCritical && reasons.length > 0) {
        skippedProtected.push({ id: memory.id, reasons });
        continue;
      }
      selected.push(memory);
    }
    for (const id of ids) {
      if (!foundIds.has(id)) {
        missingIds.push(id);
      }
    }
  } else {
    const ordered = [...anchors]
      .sort((a, b) => {
        if (a.lastConfirmedAt !== b.lastConfirmedAt) return a.lastConfirmedAt - b.lastConfirmedAt;
        if (a.updatedAt !== b.updatedAt) return a.updatedAt - b.updatedAt;
        return a.id.localeCompare(b.id);
      });
    for (const memory of ordered) {
      const reasons = protectionById.get(memory.id) || [];
      if (!allowCritical && reasons.length > 0) {
        skippedProtected.push({ id: memory.id, reasons });
        continue;
      }
      selected.push(memory);
      if (selected.length >= count) break;
    }
  }

  if (selected.length === 0) {
    if (skippedProtected.length > 0 && !allowCritical) {
      console.log(
        `Demote anchors: no eligible candidates after protection filters (skipped=${skippedProtected.length}). Re-run with --allow-critical to override.`,
      );
      skippedProtected.slice(0, 20).forEach((item) => {
        console.log(`- protected ${item.id} reasons=${item.reasons.join("|")}`);
      });
      if (skippedProtected.length > 20) {
        console.log(`...and ${skippedProtected.length - 20} more protected candidates`);
      }
      return;
    }
    console.log("Demote anchors: no matching active anchors found.");
    return;
  }

  console.log(
    `Demote anchors (${dryRun ? "dry-run" : "apply"}): selected=${selected.length} anchorsInScope=${anchors.length} targetType=${targetType} keepLatest=${keepLatest} allowCritical=${allowCritical ? "yes" : "no"}${principalId ? ` principal=${principalId}` : ""}`,
  );
  console.log(
    `Anchor governance before: anchors=${beforeGovernance.anchors}/${beforeGovernance.total} ratio=${beforeGovernance.ratio.toFixed(3)} cap=${beforeGovernance.maxCount} limit=${beforeGovernance.maxRatio.toFixed(3)} status=${beforeGovernance.exceeded ? "exceeded" : "ok"}`,
  );
  if (missingIds.length > 0) {
    console.log(`Requested ids not found in active anchor scope: ${missingIds.join(",")}`);
  }
  if (skippedProtected.length > 0 && !allowCritical) {
    console.log(`Protected anchors skipped: ${skippedProtected.length}`);
  }
  selected.slice(0, 60).forEach((memory) => {
    const reasons = protectionById.get(memory.id) || [];
    console.log(
      `- ${memory.id} status=${memory.status} source=${memory.source} confirmed=${new Date(memory.lastConfirmedAt).toISOString()}${reasons.length > 0 ? ` protected=${reasons.join("|")}` : ""} content=${memory.content}`,
    );
  });
  if (selected.length > 60) {
    console.log(`...and ${selected.length - 60} more`);
  }

  if (dryRun) {
    console.log("Dry-run only. Re-run with --apply to demote selected anchors.");
    return;
  }

  let changed = 0;
  for (const memory of selected) {
    const updated = await storage.updateMemory(memory.id, {
      memoryType: targetType,
      status: memory.status === "released" ? "released" : "active",
      requiresConfirmation: targetType !== "fact" && targetType !== "preference",
      halfLifeDays: targetHalfLifeDays(targetType),
      intentBias: targetType === "narrative" ? 0.1 : -0.75,
      source: memory.source === "import-summary" || memory.source === "system-summary"
        ? "manual-demoted-anchor"
        : memory.source,
    });
    if (updated) changed++;
  }

  await storage.flushPersistence();
  const afterMemories = await storage.getMemories();
  const afterGovernance = summarizeAnchorGovernance(afterMemories, principalId);
  console.log(`Demote anchors complete: changed=${changed}`);
  console.log(
    `Anchor governance after: anchors=${afterGovernance.anchors}/${afterGovernance.total} ratio=${afterGovernance.ratio.toFixed(3)} cap=${afterGovernance.maxCount} limit=${afterGovernance.maxRatio.toFixed(3)} status=${afterGovernance.exceeded ? "exceeded" : "ok"}`,
  );

  await appendMemoryGovernanceEvent({
    schemaVersion: MEMORY_GOVERNANCE_EVENT_SCHEMA_VERSION,
    action: "demote-anchors",
    timestamp: Date.now(),
    principalId: principalId || null,
    reason,
    targetType,
    requested: {
      ids,
      count,
      allowCritical,
      keepLatest,
    },
    beforeGovernance,
    afterGovernance,
    changed,
    selectedIds: selected.map((memory) => memory.id),
    skippedProtected,
  });
  console.log(`Governance event appended: ${MEMORY_GOVERNANCE_EVENTS_PATH}`);
}

function printHelp(): void {
  console.log("Spiral memory CLI");
  console.log("Usage:");
  console.log("  npm run memory:review -- [--context \"text\"] [--limit 50] [--all] [--json]");
  console.log("  npm run memory:prune -- [--context \"text\"] [--min-score 0.05] [--all-categories] [--dry-run]");
  console.log(
    "  npm run memory:rotate -- [--dry-run] [--apply] [--json] [--out .local/memory-rotation-report.json] [--limit 20] [--cluster <id>] [--memory <id>] [--thresholds] [--diff] [--metrics] [--semantic-preview] [--semantic-sample] [--sample-size 20] [--compute-embeddings] [--adaptive-preview] [--adaptive-apply] [--replay-check]",
  );
  console.log(
    "  npm run memory:purge -- [--source import,import-summary,system-summary] [--mode delete|release] [--principal auth:...] [--include-released] [--confirm]",
  );
  console.log(
    "  npm run memory:demote-anchors -- [--dry-run] [--apply] [--count 10] [--ids id1,id2] [--principal auth:...] [--to observation|fact|preference|interpretation|narrative|transient] [--keep-latest 1] [--allow-critical] [--reason \"quota-cleanup\"]",
  );
  console.log(
    "  npm run memory:purge-imports  # one-click purge of import/system summary memory artifacts",
  );
  console.log("  npm run memory:add -- \"memory content\"");
  console.log(
    "  npm run memory:scan-code -- [--max-files 500] [--max-items 240] [--sigil \"trace\"] [--keep-existing] [--dry-run] [--invoked]",
  );
}

async function main(): Promise<void> {
  const [command = "help", ...args] = process.argv.slice(2);

  switch (command) {
    case "review":
      await runReview(args);
      return;
    case "prune":
      await runPrune(args);
      return;
    case "purge":
      await runPurge(args);
      return;
    case "rotate":
      await runRotate(args);
      return;
    case "add":
      await runAdd(args);
      return;
    case "demote-anchors":
      await runDemoteAnchors(args);
      return;
    case "scan-code":
      await runScanCode(args);
      return;
    case "help":
    default:
      printHelp();
      if (command !== "help") {
        process.exitCode = 1;
      }
  }
}

main().catch((error) => {
  console.error("Memory CLI error:", error);
  process.exitCode = 1;
});
