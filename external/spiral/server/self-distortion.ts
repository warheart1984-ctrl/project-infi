import { createHash } from "crypto";
import { existsSync } from "fs";
import { readFile } from "fs/promises";
import path from "path";
import { evaluateRitualGate, invocationSatisfiesRitualGate } from "@shared/ritual-gate";
import { getSelfInspectionIndex } from "./self-inspection";
import { resolvePresenceEvidence } from "./prompt";
import { runSelfEvaluation } from "./self-evaluation";
import { getProjectSigil } from "./sigil-config";
import { evaluateInvocationGate } from "./veil-gate";

export type SelfDistortionProfile = "all" | "gates" | "surfaces" | "docs" | "mimicry" | "meta";
export type DistortionClass =
  | "authority-drift"
  | "asymmetry-leak"
  | "dead-declaration"
  | "thin-presence"
  | "undeclared-duplication"
  | "surface-echo";

export interface DistortionFinding {
  class: DistortionClass;
  severity: "WARN";
  note: string;
  locations: string[];
  evidence: string[];
}

export interface SelfDistortionReport {
  profile: SelfDistortionProfile;
  generatedAt: string;
  gitCommit: string | null;
  summary: {
    findings: number;
    warnings: number;
  };
  findings: DistortionFinding[];
}

const PROFILE_SET = new Set<SelfDistortionProfile>(["all", "gates", "surfaces", "docs", "mimicry", "meta"]);

const META_SCANNER_TARGETS = [
  "server/self-distortion.ts",
  "server/lib/spiral-audit.ts",
  "server/lib/output-audit.ts",
  ".spiralaudit.json",
] as const;

interface SelfDistortionProfileExecution {
  includeGates: boolean;
  includeSurfaces: boolean;
  includeDocs: boolean;
  includeMimicry: boolean;
  includeMeta: boolean;
}

interface MimicryTarget {
  id: "inspect" | "evaluate" | "distortions";
  parser: string;
  executor: string;
  commandModule: string;
  failurePrefix: string;
}

interface CommandBlockRange {
  start: number;
  end: number;
  text: string;
}

interface StringLiteralOccurrence {
  value: string;
  normalized: string;
  index: number;
  line: number;
}

const MIMICRY_TARGETS: MimicryTarget[] = [
  {
    id: "inspect",
    parser: "parseSelfInspectCommand",
    executor: "executeSelfInspectCommand",
    commandModule: "./self-inspection-command",
    failurePrefix: "Self-inspection failed:",
  },
  {
    id: "evaluate",
    parser: "parseSelfEvaluationCommand",
    executor: "executeSelfEvaluationCommand",
    commandModule: "./self-evaluation-command",
    failurePrefix: "Self-evaluation failed:",
  },
  {
    id: "distortions",
    parser: "parseSelfDistortionCommand",
    executor: "executeSelfDistortionCommand",
    commandModule: "./self-distortion-command",
    failurePrefix: "Self-distortion scan failed:",
  },
];

function normalizeWorkspacePath(value: string): string {
  return value.split(path.sep).join("/");
}

async function readWorkspaceFile(rootDir: string, relativePath: string): Promise<string> {
  return await readFile(path.join(rootDir, relativePath), "utf8");
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function hashPattern(value: string): string {
  return createHash("sha1").update(value).digest("hex").slice(0, 12);
}

function lineFromIndex(source: string, index: number): number {
  if (index <= 0) return 1;
  let lines = 1;
  for (let cursor = 0; cursor < index && cursor < source.length; cursor += 1) {
    if (source[cursor] === "\n") lines += 1;
  }
  return lines;
}

function parseNamedImportBindings(source: string): Map<string, string> {
  const bindings = new Map<string, string>();
  const importRegex = /import\s*\{([^}]+)\}\s*from\s*["']([^"']+)["'];?/g;
  let match: RegExpExecArray | null = null;
  while ((match = importRegex.exec(source)) !== null) {
    const clause = (match[1] || "").trim();
    const moduleSpecifier = (match[2] || "").trim();
    if (!clause || !moduleSpecifier) continue;
    const symbols = clause.split(",").map((entry) => entry.trim()).filter(Boolean);
    for (const symbol of symbols) {
      const [left, right] = symbol.split(/\s+as\s+/i).map((entry) => entry.trim());
      const localName = right || left;
      if (!localName) continue;
      bindings.set(localName, moduleSpecifier);
    }
  }
  return bindings;
}

function hasSharedCommandLineage(
  routesImports: Map<string, string>,
  veilImports: Map<string, string>,
  target: MimicryTarget,
): boolean {
  return (
    routesImports.get(target.parser) === target.commandModule &&
    routesImports.get(target.executor) === target.commandModule &&
    veilImports.get(target.parser) === target.commandModule &&
    veilImports.get(target.executor) === target.commandModule
  );
}

function findMatchingBrace(source: string, openingBraceIndex: number): number {
  if (openingBraceIndex < 0 || source[openingBraceIndex] !== "{") return -1;

  let depth = 0;
  let inSingle = false;
  let inDouble = false;
  let inTemplate = false;
  let escaped = false;

  for (let i = openingBraceIndex; i < source.length; i += 1) {
    const char = source[i];

    if (inSingle || inDouble || inTemplate) {
      if (escaped) {
        escaped = false;
        continue;
      }
      if (char === "\\") {
        escaped = true;
        continue;
      }
      if (inSingle && char === "'") inSingle = false;
      else if (inDouble && char === "\"") inDouble = false;
      else if (inTemplate && char === "`") inTemplate = false;
      continue;
    }

    if (char === "'") {
      inSingle = true;
      continue;
    }
    if (char === "\"") {
      inDouble = true;
      continue;
    }
    if (char === "`") {
      inTemplate = true;
      continue;
    }

    if (char === "{") {
      depth += 1;
      continue;
    }
    if (char === "}") {
      depth -= 1;
      if (depth === 0) return i;
    }
  }

  return -1;
}

function extractCommandBlockRange(source: string, parser: string): CommandBlockRange | undefined {
  const parserRegex = new RegExp(`const\\s+(\\w+)\\s*=\\s*${escapeRegex(parser)}\\([^;]*\\);`);
  const parserMatch = parserRegex.exec(source);
  if (!parserMatch?.[1] || typeof parserMatch.index !== "number") return undefined;

  const commandVar = parserMatch[1];
  const tail = source.slice(parserMatch.index);
  const guardRegex = new RegExp(`if\\s*\\(\\s*${escapeRegex(commandVar)}\\s*\\)\\s*\\{`);
  const guardMatch = guardRegex.exec(tail);
  if (!guardMatch || typeof guardMatch.index !== "number") return undefined;

  const guardStart = parserMatch.index + guardMatch.index;
  const openingBrace = source.indexOf("{", guardStart);
  if (openingBrace < 0) return undefined;

  const closingBrace = findMatchingBrace(source, openingBrace);
  if (closingBrace < 0) return undefined;

  return {
    start: guardStart,
    end: closingBrace,
    text: source.slice(guardStart, closingBrace + 1),
  };
}

function canonicalizeCommandBlock(block: string, target: MimicryTarget): string {
  const literalCollapsed = block
    .replace(/(["'])(?:\\.|(?!\1)[^\\\r\n])*\1/g, "\"<str>\"")
    .replace(/\bmessage\b/g, "<utterance>")
    .replace(/\binvocation\.utterance\b/g, "<utterance>")
    .replace(/\bself[A-Za-z]+(?:Command|Response)\b/g, "<self-symbol>")
    .replace(/\bsendImmediateAssistantResponse\b/g, "<emit>")
    .replace(/\bsendWhisper\b/g, "<emit>")
    .replace(/\bbuildWhisper\b/g, "<emit-envelope>")
    .replace(/\bpresenceLevel\b/g, "<presence>")
    .replace(new RegExp(`\\b${escapeRegex(target.parser)}\\b`, "g"), "<parser>")
    .replace(new RegExp(`\\b${escapeRegex(target.executor)}\\b`, "g"), "<executor>");

  return literalCollapsed.replace(/\s+/g, " ").trim();
}

function extractStringLiterals(source: string): StringLiteralOccurrence[] {
  const result: StringLiteralOccurrence[] = [];
  const literalRegex = /(["'])(?:\\.|(?!\1)[^\\\r\n]){24,}\1/g;
  let match: RegExpExecArray | null = null;

  while ((match = literalRegex.exec(source)) !== null) {
    const rawLiteral = match[0] || "";
    const value = rawLiteral.slice(1, -1).trim();
    if (!value) continue;
    if (!/[A-Za-z]/.test(value)) continue;
    if (!/\s/.test(value)) continue;
    if (value.includes("${")) continue;

    const normalized = value.replace(/\s+/g, " ").trim();
    const wordCount = normalized.split(/\s+/).length;
    if (wordCount < 3) continue;
    if (normalized.length > 180) continue;

    result.push({
      value,
      normalized,
      index: match.index,
      line: lineFromIndex(source, match.index),
    });
  }

  return result;
}

function indexInAnyRange(index: number, ranges: CommandBlockRange[]): boolean {
  return ranges.some((range) => index >= range.start && index <= range.end);
}

function summarizeSnippet(value: string, max = 72): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= max) return normalized;
  return `${normalized.slice(0, max - 1)}…`;
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

function buildFinding(
  className: DistortionClass,
  note: string,
  locations: string[],
  evidence: string[],
): DistortionFinding {
  return {
    class: className,
    severity: "WARN",
    note,
    locations: locations.map((entry) => normalizeWorkspacePath(entry)),
    evidence,
  };
}

function resolveSigilLocation(rootDir: string): string {
  return existsSync(path.join(rootDir, ".sigil.json")) ? ".sigil.json" : "shared/sigil.ts";
}

export function resolveSelfDistortionProfileExecution(
  profile: SelfDistortionProfile,
): SelfDistortionProfileExecution {
  return {
    includeGates: profile === "all" || profile === "gates",
    includeSurfaces: profile === "all" || profile === "surfaces",
    includeDocs: profile === "all" || profile === "docs",
    includeMimicry: profile === "all" || profile === "mimicry",
    includeMeta: profile === "meta",
  };
}

function scanThinPresenceExposure(
  rootDir: string,
  activeVeilModulePath: string,
): DistortionFinding[] {
  const projectSigil = getProjectSigil();
  const lexicalSamples = ["Present.", "Witness: Present."] as const;
  const routeRitualGate = evaluateRitualGate(projectSigil, null);
  const evidence: string[] = [];
  const locations = new Set<string>(["server/prompt.ts", resolveSigilLocation(rootDir)]);

  for (const sample of lexicalSamples) {
    const lexicalInput = {
      utterance: sample,
      trace: "",
      echo: "",
      seal: "",
    };
    if (resolvePresenceEvidence(lexicalInput) !== "lexical") {
      continue;
    }

    const invocationGate = evaluateInvocationGate(projectSigil.invocationGate, lexicalInput);
    const routeAllowed =
      invocationGate.allowed &&
      (!routeRitualGate.required ||
        invocationSatisfiesRitualGate({ message: sample }, routeRitualGate.acceptedTokens));
    const veilAllowed = invocationGate.allowed;

    if (routeAllowed) {
      locations.add("server/routes.ts");
      evidence.push(`surface=http sample=${sample}`);
    }
    if (veilAllowed) {
      locations.add(activeVeilModulePath);
      evidence.push(`surface=veil sample=${sample}`);
    }
  }

  if (evidence.length === 0) {
    return [];
  }

  evidence.push(`invocationGate.enabled=${projectSigil.invocationGate.enabled ? "yes" : "no"}`);
  evidence.push(
    `invocationGate.requireTraceSeal=${projectSigil.invocationGate.requireTraceSeal ? "yes" : "no"}`,
  );
  evidence.push(`ritualGate.required.default=${routeRitualGate.required ? "yes" : "no"}`);

  return [
    buildFinding(
      "thin-presence",
      "Lexical-only presence can clear downstream authority without structural corroboration.",
      Array.from(locations),
      evidence,
    ),
  ];
}

async function scanAuthorityDrift(
  rootDir: string,
  activeVeilModulePath: string,
): Promise<DistortionFinding[]> {
  const [routesSource, veilSource] = await Promise.all([
    readWorkspaceFile(rootDir, "server/routes.ts"),
    readWorkspaceFile(rootDir, activeVeilModulePath),
  ]);
  const gateAuthoritySymbols = ["hasValidPresence", "evaluateInvocationGate"];
  const sharedSymbols = gateAuthoritySymbols.filter((symbol) => {
    const regex = new RegExp(`\\b${symbol}\\s*\\(`);
    return regex.test(routesSource) && regex.test(veilSource);
  });
  if (sharedSymbols.length === 0) {
    return [];
  }

  return [
    buildFinding(
      "authority-drift",
      "Shared authority symbols appear across multiple invocation surfaces.",
      ["server/routes.ts", activeVeilModulePath],
      [
        `symbols=${sharedSymbols.join(",")}`,
        `surface.count=2`,
      ],
    ),
  ];
}

async function scanAsymmetryLeak(
  rootDir: string,
  activeVeilModulePath: string,
): Promise<DistortionFinding[]> {
  const [routesSource, veilSource] = await Promise.all([
    readWorkspaceFile(rootDir, "server/routes.ts"),
    readWorkspaceFile(rootDir, activeVeilModulePath),
  ]);

  const routesMarkers = {
    inspect: routesSource.indexOf("const selfInspectCommand = parseSelfInspectCommand(message);"),
    evaluate: routesSource.indexOf("const selfEvaluationCommand = parseSelfEvaluationCommand(message);"),
    distortions: routesSource.indexOf(
      "const selfDistortionCommand = parseSelfDistortionCommand(message);",
    ),
    memory: routesSource.indexOf("const memoryCommand = parseMemoryCommand(message);"),
    llm: routesSource.indexOf("const promptMetadata = await detectPromptMetadata("),
  };
  const veilMarkers = {
    inspect: veilSource.indexOf(
      "const selfInspectCommand = parseSelfInspectCommand(invocation.utterance);",
    ),
    evaluate: veilSource.indexOf(
      "const selfEvaluationCommand = parseSelfEvaluationCommand(invocation.utterance);",
    ),
    distortions: veilSource.indexOf(
      "const selfDistortionCommand = parseSelfDistortionCommand(invocation.utterance);",
    ),
    memory: veilSource.indexOf("const memoryCommand = parseMemoryCommand(invocation.utterance);"),
    llm: veilSource.indexOf("const whisper = await buildInvocationReply("),
  };

  const routesOrdered =
    routesMarkers.inspect >= 0 &&
    routesMarkers.evaluate > routesMarkers.inspect &&
    routesMarkers.distortions > routesMarkers.evaluate &&
    routesMarkers.memory > routesMarkers.distortions &&
    routesMarkers.llm > routesMarkers.memory;
  const veilOrdered =
    veilMarkers.inspect >= 0 &&
    veilMarkers.evaluate > veilMarkers.inspect &&
    veilMarkers.distortions > veilMarkers.evaluate &&
    veilMarkers.memory > veilMarkers.distortions &&
    veilMarkers.llm > veilMarkers.memory;

  if (routesOrdered && veilOrdered) {
    return [];
  }

  return [
    buildFinding(
      "asymmetry-leak",
      "Surface command ordering differs or command dispatch markers are missing.",
      ["server/routes.ts", activeVeilModulePath],
      [
        `routes.order=${routesOrdered ? "ok" : "mismatch"}`,
        `veil.order=${veilOrdered ? "ok" : "mismatch"}`,
        `routes.markers=${JSON.stringify(routesMarkers)}`,
        `veil.markers=${JSON.stringify(veilMarkers)}`,
      ],
    ),
  ];
}

async function scanDeadDeclaration(rootDir: string): Promise<DistortionFinding[]> {
  const integrityReport = await runSelfEvaluation("integrity", rootDir);
  const docsCheck = integrityReport.checks.find(
    (check) => check.id === "documentation-symbol-resolution",
  );
  if (docsCheck?.pass !== false) {
    return [];
  }
  return [
    buildFinding(
      "dead-declaration",
      "Documented declarations are not fully enforced by reachable code paths.",
      ["README.machine.md", "server/routes.ts"],
      docsCheck.evidence,
    ),
  ];
}

function scanBehavioralMimicry(
  routesSource: string,
  veilSource: string,
  activeVeilModulePath: string,
  routesImports: Map<string, string>,
  veilImports: Map<string, string>,
): DistortionFinding[] {
  const findings: DistortionFinding[] = [];

  for (const target of MIMICRY_TARGETS) {
    const routesBlock = extractCommandBlockRange(routesSource, target.parser);
    const veilBlock = extractCommandBlockRange(veilSource, target.parser);
    if (!routesBlock || !veilBlock) continue;

    const routesSignature = canonicalizeCommandBlock(routesBlock.text, target);
    const veilSignature = canonicalizeCommandBlock(veilBlock.text, target);
    if (!routesSignature || routesSignature !== veilSignature) continue;

    const sharedLineage = hasSharedCommandLineage(routesImports, veilImports, target);
    if (sharedLineage) continue;

    findings.push(
      buildFinding(
        "undeclared-duplication",
        "Behavioral duplication repeats across invocation surfaces without declared shared command lineage.",
        [
          `server/routes.ts:${lineFromIndex(routesSource, routesBlock.start)}`,
          `${activeVeilModulePath}:${lineFromIndex(veilSource, veilBlock.start)}`,
        ],
        [
          `target=${target.id}`,
          `pattern.hash=${hashPattern(routesSignature)}`,
          `lineage=none`,
        ],
      ),
    );
  }

  return findings;
}

function scanTokenMimicry(
  routesSource: string,
  veilSource: string,
  activeVeilModulePath: string,
  routesImports: Map<string, string>,
  veilImports: Map<string, string>,
): DistortionFinding[] {
  const findings: DistortionFinding[] = [];
  const routesLiterals = extractStringLiterals(routesSource);
  const veilLiterals = extractStringLiterals(veilSource);
  if (routesLiterals.length === 0 || veilLiterals.length === 0) {
    return findings;
  }

  const sharedLineageRanges = MIMICRY_TARGETS.filter((target) =>
    hasSharedCommandLineage(routesImports, veilImports, target),
  );
  const routesLineageRanges = sharedLineageRanges
    .map((target) => extractCommandBlockRange(routesSource, target.parser))
    .filter((value): value is CommandBlockRange => Boolean(value));
  const veilLineageRanges = sharedLineageRanges
    .map((target) => extractCommandBlockRange(veilSource, target.parser))
    .filter((value): value is CommandBlockRange => Boolean(value));

  const routesByToken = new Map<string, StringLiteralOccurrence[]>();
  for (const literal of routesLiterals) {
    const bucket = routesByToken.get(literal.normalized) || [];
    bucket.push(literal);
    routesByToken.set(literal.normalized, bucket);
  }

  const veilByToken = new Map<string, StringLiteralOccurrence[]>();
  for (const literal of veilLiterals) {
    const bucket = veilByToken.get(literal.normalized) || [];
    bucket.push(literal);
    veilByToken.set(literal.normalized, bucket);
  }

  const sharedTokens = Array.from(routesByToken.keys())
    .filter((token) => veilByToken.has(token))
    .sort((a, b) => b.length - a.length);

  for (const token of sharedTokens) {
    const routeCandidate = (routesByToken.get(token) || []).find(
      (entry) => !indexInAnyRange(entry.index, routesLineageRanges),
    );
    const veilCandidate = (veilByToken.get(token) || []).find(
      (entry) => !indexInAnyRange(entry.index, veilLineageRanges),
    );
    if (!routeCandidate || !veilCandidate) continue;

    findings.push(
      buildFinding(
        "undeclared-duplication",
        "Lexical convergence appears across invocation surfaces without declared shared constant lineage.",
        [
          `server/routes.ts:${routeCandidate.line}`,
          `${activeVeilModulePath}:${veilCandidate.line}`,
        ],
        [
          `pattern.hash=${hashPattern(token.toLowerCase())}`,
          `token.words=${token.split(/\s+/).length}`,
          `token.sample=${summarizeSnippet(token)}`,
          `lineage=none`,
        ],
      ),
    );

    if (findings.length >= 3) break;
  }

  return findings;
}

function scanSurfaceEchoMimicry(
  routesSource: string,
  veilSource: string,
  activeVeilModulePath: string,
  routesImports: Map<string, string>,
  veilImports: Map<string, string>,
): DistortionFinding[] {
  const findings: DistortionFinding[] = [];

  for (const target of MIMICRY_TARGETS) {
    const routesFailureIndex = routesSource.indexOf(target.failurePrefix);
    const veilFailureIndex = veilSource.indexOf(target.failurePrefix);
    if (routesFailureIndex < 0 || veilFailureIndex < 0) continue;

    const sharedLineage = hasSharedCommandLineage(routesImports, veilImports, target);
    const routesLocalOverride =
      new RegExp(`\\bfunction\\s+${escapeRegex(target.parser)}\\s*\\(`).test(routesSource) ||
      new RegExp(`\\bfunction\\s+${escapeRegex(target.executor)}\\s*\\(`).test(routesSource);
    const veilLocalOverride =
      new RegExp(`\\bfunction\\s+${escapeRegex(target.parser)}\\s*\\(`).test(veilSource) ||
      new RegExp(`\\bfunction\\s+${escapeRegex(target.executor)}\\s*\\(`).test(veilSource);

    if (sharedLineage && !routesLocalOverride && !veilLocalOverride) continue;

    findings.push(
      buildFinding(
        "surface-echo",
        "Response envelopes converge across surfaces without a complete shared command lineage declaration.",
        [
          `server/routes.ts:${lineFromIndex(routesSource, routesFailureIndex)}`,
          `${activeVeilModulePath}:${lineFromIndex(veilSource, veilFailureIndex)}`,
        ],
        [
          `target=${target.id}`,
          `shared.command.import=${sharedLineage ? "yes" : "no"}`,
          `routes.local.override=${routesLocalOverride ? "yes" : "no"}`,
          `veil.local.override=${veilLocalOverride ? "yes" : "no"}`,
          `pattern.hash=${hashPattern(target.failurePrefix.toLowerCase())}`,
        ],
      ),
    );
  }

  return findings;
}

async function scanMimicry(
  rootDir: string,
  activeVeilModulePath: string,
): Promise<DistortionFinding[]> {
  const [routesSource, veilSource] = await Promise.all([
    readWorkspaceFile(rootDir, "server/routes.ts"),
    readWorkspaceFile(rootDir, activeVeilModulePath),
  ]);
  const routesImports = parseNamedImportBindings(routesSource);
  const veilImports = parseNamedImportBindings(veilSource);

  return [
    ...scanBehavioralMimicry(
      routesSource,
      veilSource,
      activeVeilModulePath,
      routesImports,
      veilImports,
    ),
    ...scanTokenMimicry(
      routesSource,
      veilSource,
      activeVeilModulePath,
      routesImports,
      veilImports,
    ),
    ...scanSurfaceEchoMimicry(
      routesSource,
      veilSource,
      activeVeilModulePath,
      routesImports,
      veilImports,
    ),
  ];
}

async function scanMeta(rootDir: string): Promise<{
  findings: DistortionFinding[];
  targetEvidence: string[];
}> {
  const findings: DistortionFinding[] = [];
  const targetEvidence: string[] = [];

  for (const relativePath of META_SCANNER_TARGETS) {
    const absolutePath = path.join(rootDir, relativePath);
    if (existsSync(absolutePath)) {
      const source = await readWorkspaceFile(rootDir, relativePath);
      targetEvidence.push(`target=${relativePath} bytes=${source.length}`);
      continue;
    }

    findings.push(
      buildFinding(
        "dead-declaration",
        "Meta scanner target is missing from the hardcoded scanner surface.",
        [relativePath],
        [
          `target=${relativePath}`,
          "target.missing=yes",
          `target.count=${META_SCANNER_TARGETS.length}`,
        ],
      ),
    );
  }

  return {
    findings,
    targetEvidence,
  };
}

export function isSelfDistortionProfile(value: string): value is SelfDistortionProfile {
  return PROFILE_SET.has(value as SelfDistortionProfile);
}

export async function runSelfDistortionScan(
  profile: SelfDistortionProfile = "all",
  rootDir = process.cwd(),
): Promise<SelfDistortionReport> {
  const [inspectionIndex, activeVeilModulePath] = await Promise.all([
    getSelfInspectionIndex({ rootDir }),
    resolveActiveVeilModulePath(rootDir),
  ]);
  const findings: DistortionFinding[] = [];
  let metaTargetEvidence: string[] = [];
  const execution = resolveSelfDistortionProfileExecution(profile);

  if (execution.includeGates) {
    findings.push(...(await scanAuthorityDrift(rootDir, activeVeilModulePath)));
    findings.push(...scanThinPresenceExposure(rootDir, activeVeilModulePath));
  }
  if (execution.includeSurfaces) {
    findings.push(...(await scanAsymmetryLeak(rootDir, activeVeilModulePath)));
  }
  if (execution.includeDocs) {
    findings.push(...(await scanDeadDeclaration(rootDir)));
  }
  if (execution.includeMimicry) {
    findings.push(...(await scanMimicry(rootDir, activeVeilModulePath)));
  }
  if (execution.includeMeta) {
    const metaScan = await scanMeta(rootDir);
    findings.push(...metaScan.findings);
    metaTargetEvidence = metaScan.targetEvidence;
  }

  const report: SelfDistortionReport = {
    profile,
    generatedAt: new Date().toISOString(),
    gitCommit: inspectionIndex.gitCommit,
    summary: {
      findings: findings.length,
      warnings: findings.length,
    },
    findings,
  };

  if (execution.includeMeta) {
    const rendered = formatSelfDistortionReport(report);
    if (/\bmeta\b/i.test(rendered)) {
      findings.push(
        buildFinding(
          "surface-echo",
          "Witness mark: meta profile name appears in rendered meta output; boundary held without chaining.",
          ["server/self-distortion.ts"],
          [
            "profile=meta",
            "witness=output-self-name",
            "chain=none",
            `target.count=${META_SCANNER_TARGETS.length}`,
            ...metaTargetEvidence,
          ],
        ),
      );
      report.summary.findings = findings.length;
      report.summary.warnings = findings.length;
    }
  }

  return report;
}

export function formatSelfDistortionReport(report: SelfDistortionReport): string {
  const lines = [
    `Distortion scan: ${report.profile}`,
    `Findings: ${report.summary.findings}`,
  ];
  if (report.findings.length === 0) {
    lines.push("");
    lines.push("No structural distortions detected.");
    return lines.join("\n");
  }

  for (const finding of report.findings) {
    lines.push("");
    lines.push(`[${finding.severity}] ${finding.class}`);
    lines.push(`  Locations: ${finding.locations.join(", ")}`);
    lines.push(`  Note: ${finding.note}`);
    for (const item of finding.evidence) {
      lines.push(`  - ${item}`);
    }
  }

  return lines.join("\n");
}
