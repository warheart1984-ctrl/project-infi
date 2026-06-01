import { execFileSync } from "child_process";
import { readFile, readdir, stat } from "fs/promises";
import path from "path";

type ExportKind = "function" | "const" | "class" | "type" | "interface" | "enum" | "named";
type MatchKind = "export" | "path" | "comment" | "import";

const DEFAULT_INCLUDE_DIRS = ["server", "shared", "script", "client/src"];
const SOURCE_EXTENSIONS = new Set([".ts", ".tsx", ".js", ".jsx"]);
const IGNORED_DIRS = new Set([
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
const MAX_FILES = Math.max(
  200,
  Number.parseInt(process.env.SELF_INSPECT_MAX_FILES || "1600", 10) || 1600,
);
const MAX_FILE_BYTES = Math.max(
  8_192,
  Number.parseInt(process.env.SELF_INSPECT_MAX_FILE_BYTES || "300000", 10) || 300_000,
);
const MAX_COMMENTS_PER_FILE = Math.max(
  3,
  Number.parseInt(process.env.SELF_INSPECT_MAX_COMMENTS_PER_FILE || "8", 10) || 8,
);
const CACHE_TTL_MS = Math.max(
  1_000,
  Number.parseInt(process.env.SELF_INSPECT_CACHE_TTL_MS || "120000", 10) || 120_000,
);
const DEFAULT_QUERY_LIMIT = Math.max(
  1,
  Number.parseInt(process.env.SELF_INSPECT_QUERY_LIMIT || "12", 10) || 12,
);

export interface SelfInspectExport {
  kind: ExportKind;
  name: string;
  line: number;
}

export interface SelfInspectFileIndex {
  path: string;
  bytes: number;
  exports: SelfInspectExport[];
  imports: string[];
  comments: string[];
}

export interface SelfInspectionIndex {
  generatedAt: string;
  rootDir: string;
  gitCommit: string | null;
  includeDirs: string[];
  fileCount: number;
  symbolCount: number;
  files: SelfInspectFileIndex[];
}

export interface SelfInspectMatch {
  path: string;
  line: number;
  kind: MatchKind;
  label: string;
}

export interface SelfInspectQueryResult {
  query: string;
  totalMatches: number;
  matches: SelfInspectMatch[];
  truncated: boolean;
}

export interface BuildSelfInspectionOptions {
  rootDir?: string;
  includeDirs?: string[];
}

interface CachedSelfInspectionState {
  cacheKey: string;
  builtAt: number;
  index: SelfInspectionIndex;
}

let cachedState: CachedSelfInspectionState | undefined;

function normalizePathForIndex(filePath: string): string {
  return filePath.split(path.sep).join("/");
}

function countLine(source: string, index: number): number {
  if (index <= 0) return 1;
  let line = 1;
  for (let i = 0; i < index && i < source.length; i += 1) {
    if (source.charCodeAt(i) === 10) {
      line += 1;
    }
  }
  return line;
}

function normalizeComment(value: string): string {
  return value
    .replace(/^\/\//, "")
    .replace(/^\/\*/, "")
    .replace(/\*\/$/, "")
    .replace(/^\s*\*\s?/gm, "")
    .replace(/\s+/g, " ")
    .trim();
}

function resolveGitCommit(rootDir: string): string | null {
  try {
    const value = execFileSync("git", ["rev-parse", "--short", "HEAD"], {
      cwd: rootDir,
      stdio: ["ignore", "pipe", "ignore"],
      encoding: "utf8",
    }).trim();
    if (!value) return null;
    return value;
  } catch {
    return null;
  }
}

async function collectSourceFiles(rootDir: string, includeDirs: string[]): Promise<string[]> {
  const files: string[] = [];

  async function walk(currentDir: string): Promise<void> {
    if (files.length >= MAX_FILES) return;
    let entries: import("fs").Dirent[];
    try {
      entries = await readdir(currentDir, { withFileTypes: true, encoding: "utf8" });
    } catch {
      return;
    }

    for (const entry of entries) {
      if (files.length >= MAX_FILES) return;
      const nextPath = path.join(currentDir, entry.name);
      if (entry.isDirectory()) {
        if (IGNORED_DIRS.has(entry.name)) continue;
        await walk(nextPath);
        continue;
      }
      if (!entry.isFile()) continue;
      const ext = path.extname(entry.name).toLowerCase();
      if (!SOURCE_EXTENSIONS.has(ext)) continue;
      files.push(nextPath);
    }
  }

  for (const includeDir of includeDirs) {
    const resolved = path.join(rootDir, includeDir);
    await walk(resolved);
  }

  files.sort((a, b) => a.localeCompare(b));
  return files;
}

function pushExportMatch(
  exports: SelfInspectExport[],
  source: string,
  kind: ExportKind,
  name: string,
  index: number,
): void {
  if (!name) return;
  exports.push({
    kind,
    name,
    line: countLine(source, index),
  });
}

function extractFileIndex(relativePath: string, source: string, bytes: number): SelfInspectFileIndex {
  const exports: SelfInspectExport[] = [];
  const seenExportKey = new Set<string>();
  const importSet = new Set<string>();
  const commentSet = new Set<string>();

  const addExport = (kind: ExportKind, name: string, index: number) => {
    const key = `${kind}:${name}`;
    if (!name || seenExportKey.has(key)) return;
    seenExportKey.add(key);
    pushExportMatch(exports, source, kind, name, index);
  };

  const functionRegex = /\bexport\s+(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)/g;
  const constRegex = /\bexport\s+(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)/g;
  const classRegex = /\bexport\s+class\s+([A-Za-z_$][A-Za-z0-9_$]*)/g;
  const typeRegex = /\bexport\s+(?:type|interface|enum)\s+([A-Za-z_$][A-Za-z0-9_$]*)/g;
  const groupRegex = /\bexport\s*\{([^}]+)\}/g;
  const importRegex = /\bimport(?:["'\s\w{},*]+from\s+)?["'`]([^"'`]+)["'`]/g;
  const blockCommentRegex = /\/\*[\s\S]*?\*\//g;
  const lineCommentRegex = /\/\/[^\r\n]*/g;

  let match: RegExpExecArray | null = null;

  while ((match = functionRegex.exec(source)) !== null) {
    addExport("function", match[1], match.index);
  }
  while ((match = constRegex.exec(source)) !== null) {
    addExport("const", match[1], match.index);
  }
  while ((match = classRegex.exec(source)) !== null) {
    addExport("class", match[1], match.index);
  }
  while ((match = typeRegex.exec(source)) !== null) {
    const kindToken = source
      .slice(match.index, Math.min(source.length, match.index + 40))
      .match(/\b(type|interface|enum)\b/i)?.[1]
      ?.toLowerCase();
    const kind = kindToken === "interface" || kindToken === "type" || kindToken === "enum"
      ? (kindToken as ExportKind)
      : "type";
    addExport(kind, match[1], match.index);
  }
  while ((match = groupRegex.exec(source)) !== null) {
    const names = match[1]
      .split(",")
      .map((segment) => segment.trim())
      .map((segment) => segment.split(/\s+as\s+/i)[0]?.trim() || "")
      .filter(Boolean);
    for (const name of names) {
      addExport("named", name, match.index);
    }
  }
  while ((match = importRegex.exec(source)) !== null) {
    const moduleName = (match[1] || "").trim();
    if (moduleName) importSet.add(moduleName);
  }
  while ((match = blockCommentRegex.exec(source)) !== null) {
    const normalized = normalizeComment(match[0]);
    if (normalized) commentSet.add(normalized);
    if (commentSet.size >= MAX_COMMENTS_PER_FILE) break;
  }
  if (commentSet.size < MAX_COMMENTS_PER_FILE) {
    while ((match = lineCommentRegex.exec(source)) !== null) {
      const normalized = normalizeComment(match[0]);
      if (!normalized) continue;
      commentSet.add(normalized);
      if (commentSet.size >= MAX_COMMENTS_PER_FILE) break;
    }
  }

  return {
    path: relativePath,
    bytes,
    exports: exports.sort((a, b) => a.line - b.line),
    imports: Array.from(importSet).slice(0, 32),
    comments: Array.from(commentSet).slice(0, MAX_COMMENTS_PER_FILE),
  };
}

function buildCacheKey(rootDir: string, includeDirs: string[]): string {
  return `${normalizePathForIndex(rootDir)}::${includeDirs.join(",")}`;
}

export async function buildSelfInspectionIndex(
  options: BuildSelfInspectionOptions = {},
): Promise<SelfInspectionIndex> {
  const rootDir = options.rootDir || process.cwd();
  const includeDirs = (options.includeDirs || DEFAULT_INCLUDE_DIRS)
    .map((value) => value.trim())
    .filter(Boolean);
  const files = await collectSourceFiles(rootDir, includeDirs);
  const indexedFiles: SelfInspectFileIndex[] = [];

  for (const filePath of files) {
    let fileStats: Awaited<ReturnType<typeof stat>>;
    try {
      fileStats = await stat(filePath);
    } catch {
      continue;
    }
    if (!fileStats.isFile() || fileStats.size <= 0 || fileStats.size > MAX_FILE_BYTES) continue;

    let source = "";
    try {
      source = await readFile(filePath, "utf8");
    } catch {
      continue;
    }
    if (!source.trim()) continue;

    const relativePath = normalizePathForIndex(path.relative(rootDir, filePath));
    indexedFiles.push(extractFileIndex(relativePath, source, fileStats.size));
  }

  const symbolCount = indexedFiles.reduce((total, file) => total + file.exports.length, 0);
  return {
    generatedAt: new Date().toISOString(),
    rootDir: normalizePathForIndex(rootDir),
    gitCommit: resolveGitCommit(rootDir),
    includeDirs,
    fileCount: indexedFiles.length,
    symbolCount,
    files: indexedFiles,
  };
}

export async function getSelfInspectionIndex(options: {
  forceRefresh?: boolean;
  rootDir?: string;
  includeDirs?: string[];
} = {}): Promise<SelfInspectionIndex> {
  const rootDir = options.rootDir || process.cwd();
  const includeDirs = (options.includeDirs || DEFAULT_INCLUDE_DIRS)
    .map((value) => value.trim())
    .filter(Boolean);
  const cacheKey = buildCacheKey(rootDir, includeDirs);
  const now = Date.now();

  if (!options.forceRefresh && cachedState && cachedState.cacheKey === cacheKey) {
    if (now - cachedState.builtAt <= CACHE_TTL_MS) {
      return cachedState.index;
    }
  }

  const index = await buildSelfInspectionIndex({ rootDir, includeDirs });
  cachedState = {
    cacheKey,
    builtAt: now,
    index,
  };
  return index;
}

function pushMatch(
  bucket: SelfInspectMatch[],
  pathValue: string,
  line: number,
  kind: MatchKind,
  label: string,
): void {
  bucket.push({
    path: pathValue,
    line: Math.max(1, line),
    kind,
    label,
  });
}

export async function querySelfInspection(
  rawQuery: string,
  options: {
    limit?: number;
    forceRefresh?: boolean;
    rootDir?: string;
    includeDirs?: string[];
  } = {},
): Promise<SelfInspectQueryResult> {
  const query = rawQuery.trim().toLowerCase();
  const limit = Math.max(1, options.limit || DEFAULT_QUERY_LIMIT);
  const index = await getSelfInspectionIndex({
    forceRefresh: options.forceRefresh,
    rootDir: options.rootDir,
    includeDirs: options.includeDirs,
  });

  if (!query) {
    return {
      query: rawQuery,
      totalMatches: 0,
      matches: [],
      truncated: false,
    };
  }

  const allMatches: SelfInspectMatch[] = [];
  for (const file of index.files) {
    const normalizedPath = file.path.toLowerCase();
    if (normalizedPath.includes(query)) {
      pushMatch(allMatches, file.path, 1, "path", file.path);
    }

    for (const symbol of file.exports) {
      if (symbol.name.toLowerCase().includes(query)) {
        pushMatch(
          allMatches,
          file.path,
          symbol.line,
          "export",
          `${symbol.kind} ${symbol.name}`,
        );
      }
    }

    for (const moduleName of file.imports) {
      if (moduleName.toLowerCase().includes(query)) {
        pushMatch(allMatches, file.path, 1, "import", `import ${moduleName}`);
      }
    }

    for (const comment of file.comments) {
      if (comment.toLowerCase().includes(query)) {
        pushMatch(allMatches, file.path, 1, "comment", comment);
      }
    }
  }

  allMatches.sort((a, b) => {
    if (a.path !== b.path) return a.path.localeCompare(b.path);
    if (a.line !== b.line) return a.line - b.line;
    return a.label.localeCompare(b.label);
  });

  return {
    query: rawQuery,
    totalMatches: allMatches.length,
    matches: allMatches.slice(0, limit),
    truncated: allMatches.length > limit,
  };
}

export function formatSelfInspectionSummary(index: SelfInspectionIndex): string {
  const topFiles = [...index.files]
    .sort((a, b) => b.exports.length - a.exports.length)
    .slice(0, 5)
    .map((file) => `- ${file.path} (exports: ${file.exports.length}, comments: ${file.comments.length})`);
  const lines = [
    "Self-inspection index is ready.",
    `Git commit: ${index.gitCommit || "unavailable"}`,
    `Indexed files: ${index.fileCount}`,
    `Exported symbols: ${index.symbolCount}`,
    `Included roots: ${index.includeDirs.join(", ")}`,
  ];
  if (topFiles.length > 0) {
    lines.push("Top symbol files:");
    lines.push(...topFiles);
  }
  lines.push('Use "self inspect <query>" for targeted lookups.');
  return lines.join("\n");
}

export function formatSelfInspectionQuery(result: SelfInspectQueryResult): string {
  if (!result.query.trim()) {
    return 'Provide a query, for example: "self inspect auth".';
  }
  if (result.totalMatches === 0) {
    return `No structural matches found for "${result.query.trim()}".`;
  }

  const lines = [
    `Self-inspection matches for "${result.query.trim()}": ${result.totalMatches}`,
  ];
  for (const match of result.matches) {
    lines.push(`- ${match.path}:${match.line} [${match.kind}] ${match.label}`);
  }
  if (result.truncated) {
    lines.push(`...truncated to ${result.matches.length} entries.`);
  }
  return lines.join("\n");
}
