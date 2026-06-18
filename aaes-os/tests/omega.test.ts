import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DefaultActionEngine } from "../src/pipeline/action_engine.js";
import { DefaultDeliberationEngine } from "../src/pipeline/deliberation.js";
import { DefaultInvariantEngine } from "../src/engines/invariant_engine.js";
import { DefaultPerceptionEngine } from "../src/pipeline/perception.js";
import { DefaultPlanningEngine } from "../src/pipeline/planning.js";
import { DefaultPolicyEngine } from "../src/engines/policy_engine.js";
import { ConsoleAuditLogger } from "../src/governance/audit_logger.js";
import { DanielModule } from "../src/modules/daniel/module.js";
import { AAESOrchestrator } from "../src/orchestrator.js";
import { InMemoryTraceStore } from "../src/storage/trace_store.js";
import type { AAESAction, AAESContext, AAESRequest } from "../src/types.js";
import { createStep, newTraceId } from "../src/types.js";

function validRequest(overrides: Partial<AAESRequest> = {}): AAESRequest {
  return {
    actorId: "operator-omega",
    scope: { name: "code" },
    prompt: "implement code fix",
    ...overrides,
  };
}

function buildOrchestrator(traceStore = new InMemoryTraceStore()): AAESOrchestrator {
  const auditLogger = new ConsoleAuditLogger(traceStore);
  const policyEngine = new DefaultPolicyEngine();
  return new AAESOrchestrator({
    invariantEngine: new DefaultInvariantEngine(),
    perceptionEngine: new DefaultPerceptionEngine(),
    deliberationEngine: new DefaultDeliberationEngine(),
    planningEngine: new DefaultPlanningEngine(),
    actionEngine: new DefaultActionEngine({
      policyEngine,
      modules: [new DanielModule()],
    }),
    auditLogger,
  });
}

describe("omega adversarial", () => {
  it("blocks missing actorId at invariant gate", async () => {
    const orch = buildOrchestrator();
    const result = await orch.handle(validRequest({ actorId: "" }));
    assert.equal(result.ok, false);
    assert.match(result.error?.code ?? "", /AAES_IDENTITY_INVALID|AAES_INVARIANT_BLOCK/);
  });

  it("blocks missing scope at invariant gate", async () => {
    const orch = buildOrchestrator();
    const result = await orch.handle(validRequest({ scope: undefined }));
    assert.equal(result.ok, false);
    assert.match(result.error?.code ?? "", /AAES_SCOPE_MISSING|AAES_INVARIANT_BLOCK/);
  });

  it("blocks missing scope.name at invariant gate", async () => {
    const orch = buildOrchestrator();
    const result = await orch.handle(validRequest({ scope: { name: "" } }));
    assert.equal(result.ok, false);
    assert.match(result.error?.code ?? "", /AAES_SCOPE_MISSING|AAES_INVARIANT_BLOCK/);
  });

  it("invariant engine rejects empty traceId on context", () => {
    const engine = new DefaultInvariantEngine();
    const ctx: AAESContext = {
      traceId: "",
      request: validRequest(),
      session: {},
      steps: [],
      metadata: {},
    };
    const result = engine.evaluate(ctx);
    assert.equal(result.allowed, false);
    assert.ok(result.violations.some((v) => v.code === "AAES_TRACE_MISSING"));
  });

  it("denies daniel.code when scope.name is not code", async () => {
    const orch = buildOrchestrator();
    const result = await orch.handle(
      validRequest({
        scope: { name: "analyze" },
        prompt: "implement the refactor in code",
      }),
    );
    assert.equal(result.ok, true);
    assert.ok(result.results.length >= 1);
    assert.equal(result.results[0]?.status, "denied");
    assert.match(result.results[0]?.error ?? "", /daniel\.code denied/);
  });

  it("allows daniel.code when scope.name is code", async () => {
    const traceStore = new InMemoryTraceStore();
    const orch = buildOrchestrator(traceStore);
    const result = await orch.handle(validRequest({ scope: { name: "code" } }));
    assert.equal(result.ok, true);
    assert.equal(result.results[0]?.status, "success");

    const trace = traceStore.getTrace(result.traceId);
    assert.ok(trace);
    assert.ok(trace.steps.length >= 3);
  });

  it("policy engine denies daniel.code action outside code scope", () => {
    const policy = new DefaultPolicyEngine();
    const action: AAESAction = {
      actionId: "a1",
      target: "daniel.code",
      operation: "execute",
      args: {},
    };
    const ctx: AAESContext = {
      traceId: newTraceId(),
      request: validRequest({ scope: { name: "ops" } }),
      session: {},
      steps: [],
      metadata: {},
    };
    const result = policy.evaluate(ctx.request, ctx, action);
    assert.equal(result.allowed, false);
    assert.equal(result.code, "AAES_POLICY_DENIED");
  });

  it("DanielModule only handles daniel.* targets", () => {
    const mod = new DanielModule();
    assert.equal(
      mod.canHandle({ actionId: "1", target: "daniel.code", operation: "execute", args: {} }),
      true,
    );
    assert.equal(
      mod.canHandle({ actionId: "2", target: "filesystem", operation: "write", args: {} }),
      false,
    );
  });

  it("DanielModule execute returns module, target, parameters", async () => {
    const mod = new DanielModule();
    const result = await mod.execute({
      actionId: "1",
      target: "daniel.code",
      operation: "execute",
      args: { description: "patch" },
    });
    assert.equal(result.status, "success");
    const output = result.output as { module: string; target: string; parameters: unknown };
    assert.equal(output.module, "daniel");
    assert.equal(output.target, "daniel.code");
    assert.deepEqual(output.parameters, { description: "patch" });
  });

  it("aborts pipeline on invariant block before perception side effects recorded", async () => {
    const traceStore = new InMemoryTraceStore();
    const orch = buildOrchestrator(traceStore);
    const result = await orch.handle(validRequest({ actorId: "" }));
    assert.equal(result.ok, false);
    const trace = traceStore.getTrace(result.traceId);
    assert.ok(trace);
    const types = trace.steps.map((s) => s.stepType);
    assert.ok(types.includes("ingress"));
    assert.equal(types.includes("perception"), false);
  });

  it("invariant blocks steps missing stepId", () => {
    const engine = new DefaultInvariantEngine();
    const ctx: AAESContext = {
      traceId: newTraceId(),
      request: validRequest(),
      session: {},
      steps: [],
      metadata: {},
    };
    const badStep = createStep("test", "bad");
    badStep.stepId = "";
    const result = engine.evaluate(ctx, badStep);
    assert.equal(result.allowed, false);
  });
});
