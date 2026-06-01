import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { formatSelfDistortionReport, runSelfDistortionScan } from "../server/self-distortion";
import { runSelfEvaluation } from "../server/self-evaluation";
import { resolveResponseShapePolicy } from "../server/lib/response-shape-policy";

async function readWorkspaceFile(relativePath: string): Promise<string> {
  return await readFile(new URL(`../${relativePath}`, import.meta.url), "utf8");
}

function extractStringLiterals(source: string): string[] {
  const literals: string[] = [];
  const regex = /(["'`])(?:\\.|(?!\1)[^\\\r\n])*\1/g;
  let match: RegExpExecArray | null = null;
  while ((match = regex.exec(source)) !== null) {
    const token = (match[0] || "").slice(1, -1).trim();
    if (token.length < 8) continue;
    literals.push(token);
  }
  return literals;
}

function countOccurrences(source: string, pattern: RegExp): number {
  return (source.match(pattern) || []).length;
}

test("/api/chat enforces invocation and ritual gates before command dispatch", async () => {
  const source = await readWorkspaceFile("server/routes.ts");
  const invocationGateIndex = source.indexOf("if (!invocationGate.allowed)");
  const ritualGateIndex = source.indexOf("if (!ritualGateSatisfied)");
  const selfInspectIndex = source.indexOf("const selfInspectCommand = parseSelfInspectCommand(message);");
  const ritualInvocationCheckIndex = source.indexOf("invocationSatisfiesRitualGate(");
  const memoryCommandIndex = source.indexOf("const memoryCommand = parseMemoryCommand(message);");

  assert.ok(invocationGateIndex >= 0, "Invocation gate rejection branch must exist.");
  assert.ok(ritualGateIndex >= 0, "Ritual gate rejection branch must exist.");
  assert.ok(ritualInvocationCheckIndex >= 0, "Ritual gate must evaluate invocation payload.");
  assert.ok(selfInspectIndex > ritualGateIndex, "Self-inspection dispatch must be after gate enforcement.");
  assert.ok(memoryCommandIndex > selfInspectIndex, "Memory command dispatch must remain after self commands.");
});

test("forbidden projection patterns are guarded and not hard-coded in user-facing envelopes", async () => {
  const [auditRaw, routesSource, veilSource, systemMessagesSource] = await Promise.all([
    readWorkspaceFile(".spiralaudit.json"),
    readWorkspaceFile("server/routes.ts"),
    readWorkspaceFile("server/veil-channel.mirror.ts"),
    readWorkspaceFile("server/shared/system-messages.ts"),
  ]);
  const parsedAudit = JSON.parse(auditRaw) as { forbiddenProjectionPattern?: unknown };
  const forbiddenProjectionPattern =
    typeof parsedAudit.forbiddenProjectionPattern === "string"
      ? parsedAudit.forbiddenProjectionPattern
      : "";
  assert.ok(forbiddenProjectionPattern.length > 0, ".spiralaudit.json must declare forbiddenProjectionPattern.");

  const forbiddenRegex = new RegExp(forbiddenProjectionPattern, "i");
  const literals = [
    ...extractStringLiterals(routesSource),
    ...extractStringLiterals(veilSource),
    ...extractStringLiterals(systemMessagesSource),
  ];
  const violations = literals.filter((value) => forbiddenRegex.test(value));

  assert.equal(
    violations.length,
    0,
    `User-facing literals must not include forbidden projection patterns. Found: ${violations.join(" | ")}`,
  );
});

test("Spiral-aligned declarations are backed by executable gate and ledger enforcement", async () => {
  const [auditSource, routesSource] = await Promise.all([
    readWorkspaceFile("server/lib/spiral-audit.ts"),
    readWorkspaceFile("server/routes.ts"),
  ]);
  const declaresSpiralAligned = auditSource.includes("Spiral-aligned");
  assert.equal(declaresSpiralAligned, true, "Expected Spiral-aligned declaration in audit module.");
  assert.match(routesSource, /if \(!invocationGate\.allowed\)/, "Routes must enforce invocation gate.");
  assert.match(routesSource, /if \(!ritualGateSatisfied\)/, "Routes must enforce ritual gate.");
  assert.match(routesSource, /type:\s*"gate"/, "Routes must ledger gate outcomes.");
  assert.match(routesSource, /type:\s*"response-shape"/, "Routes must ledger response-shape decisions.");
});

test("provider streaming invocations are constrained to a single choke-point helper", async () => {
  const source = await readWorkspaceFile("server/routes.ts");
  assert.match(
    source,
    /async function invokeProviderStream\s*\(/,
    "Routes must define invokeProviderStream choke-point.",
  );
  assert.equal(
    countOccurrences(source, /\bstreamOpenAI\(/g),
    2,
    "streamOpenAI should appear only as function definition and choke-point call.",
  );
  assert.equal(
    countOccurrences(source, /\bstreamAzureOpenAI\(/g),
    2,
    "streamAzureOpenAI should appear only as function definition and choke-point call.",
  );
  assert.equal(
    countOccurrences(source, /\bstreamAnthropic\(/g),
    2,
    "streamAnthropic should appear only as function definition and choke-point call.",
  );
  assert.equal(
    countOccurrences(source, /\bstreamGoogle\(/g),
    2,
    "streamGoogle should appear only as function definition and choke-point call.",
  );
});

test("governance scans fail closed for gate bypass and mimicry drift", async () => {
  const [integrity, gates, contracts, mimicry] = await Promise.all([
    runSelfEvaluation("integrity"),
    runSelfEvaluation("gates"),
    runSelfEvaluation("contracts"),
    runSelfDistortionScan("mimicry"),
  ]);

  assert.equal(integrity.summary.failed, 0, "Self-evaluation integrity profile must pass.");
  assert.equal(gates.summary.failed, 0, "Self-evaluation gates profile must pass.");
  const contractGateCheck = contracts.checks.find(
    (check) => check.id === "inspection-dispatch-precedes-recall",
  );
  assert.equal(
    contractGateCheck?.pass,
    true,
    "Contract gate-precedence check must pass under contracts profile.",
  );
  assert.equal(
    mimicry.findings.length,
    0,
    `Mimicry profile must be clean.\n${formatSelfDistortionReport(mimicry)}`,
  );
});

test("strict veil never returns full when distortions are present", () => {
  const policy = resolveResponseShapePolicy({
    audit: {
      confidence: 0.9,
      clarityOK: true,
      noMimicry: false,
    },
    minConfidence: 0.6,
    veilBehavior: "strict",
    truncated: false,
  });

  assert.notEqual(
    policy.decision,
    "full",
    "Strict veil must not allow full output when distortion findings exist.",
  );
});
