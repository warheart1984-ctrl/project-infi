import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { compilePlanToActions, DefaultActionEngine } from "../src/pipeline/action_engine.js";
import { DefaultDeliberationEngine } from "../src/pipeline/deliberation.js";
import { DefaultPerceptionEngine } from "../src/pipeline/perception.js";
import { DefaultPlanningEngine } from "../src/pipeline/planning.js";
import { DefaultPolicyEngine } from "../src/engines/policy_engine.js";
import { DanielModule } from "../src/modules/daniel/module.js";
import { normalizeInput } from "../src/uls/normalize.js";
import type { AAESContext, AAESPlan, AAESRequest } from "../src/types.js";
import { newTraceId } from "../src/types.js";

function baseContext(request: Partial<AAESRequest> = {}): AAESContext {
  const full: AAESRequest = {
    actorId: "operator-1",
    scope: { name: "code" },
    prompt: "implement fix for login bug",
    ...request,
  };
  return {
    traceId: full.traceId ?? newTraceId(),
    request: full,
    session: {},
    steps: [],
    metadata: {},
  };
}

describe("pipeline", () => {
  it("normalizeInput infers code_change intent", () => {
    const norm = normalizeInput("please implement the auth fix in code");
    assert.equal(norm.intent, "code_change");
  });

  it("DefaultPerceptionEngine sets ctx.session.normalized", () => {
    const ctx = baseContext();
    const engine = new DefaultPerceptionEngine();
    engine.perceive(ctx);
    assert.ok(ctx.session.normalized);
    assert.equal(ctx.session.normalized?.intent, "code_change");
  });

  it("DefaultDeliberationEngine uses normalized intent and daniel.code plan", () => {
    const ctx = baseContext();
    new DefaultPerceptionEngine().perceive(ctx);
    const { plans } = new DefaultDeliberationEngine().deliberate(ctx);
    assert.ok(plans.length >= 1);
    const codePlan = plans.find((p) => p.intent === "code_change");
    assert.ok(codePlan);
    assert.equal(codePlan.steps[0]?.kind, "daniel.code");
  });

  it("DefaultPlanningEngine selects plan matching intent", () => {
    const ctx = baseContext();
    new DefaultPerceptionEngine().perceive(ctx);
    const { plans } = new DefaultDeliberationEngine().deliberate(ctx);
    const { decision } = new DefaultPlanningEngine().selectPlan(ctx, plans);
    assert.equal(decision.blocked, false);
    assert.equal(decision.selectedPlan?.intent, "code_change");
  });

  it("compilePlanToActions maps daniel.code kind to action target", () => {
    const plan: AAESPlan = {
      planId: "plan_test",
      intent: "code_change",
      steps: [{ id: "1", kind: "daniel.code", description: "patch" }],
    };
    const actions = compilePlanToActions(plan);
    assert.equal(actions.length, 1);
    assert.equal(actions[0]?.target, "daniel.code");
    assert.equal(actions[0]?.operation, "execute");
  });

  it("DefaultActionEngine runs DanielModule when policy allows", async () => {
    const ctx = baseContext({ scope: { name: "code" } });
    new DefaultPerceptionEngine().perceive(ctx);
    const { plans } = new DefaultDeliberationEngine().deliberate(ctx);
    const { decision } = new DefaultPlanningEngine().selectPlan(ctx, plans);

    const engine = new DefaultActionEngine({
      policyEngine: new DefaultPolicyEngine(),
      modules: [new DanielModule()],
    });

    const { results } = await engine.run(ctx, decision);
    assert.equal(results.length, 1);
    assert.equal(results[0]?.status, "success");
    assert.equal((results[0]?.output as { module?: string }).module, "daniel");
  });
});
