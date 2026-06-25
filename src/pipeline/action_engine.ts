/**
 * Mythic: Action runner
 * Engineering: DefaultActionEngine, compilePlanToActions
 */

import type { PolicyEngine } from "../engines/policy_engine.js";
import type { ExecutionModule } from "../modules/daniel/module.js";
import type {
  AAESAction,
  AAESContext,
  AAESDecision,
  AAESPlan,
  AAESStep,
  ActionResult,
  AuditLogger,
} from "../types.js";
import { createStep } from "../types.js";

export interface ActionEngine {
  run(ctx: AAESContext, decision: AAESDecision): Promise<{ step: AAESStep; results: ActionResult[] }>;
}

export interface ActionEngineDeps {
  policyEngine: PolicyEngine;
  modules: ExecutionModule[];
  auditLogger?: AuditLogger;
}

export function compilePlanToActions(plan: AAESPlan): AAESAction[] {
  return plan.steps.map((step) => ({
    actionId: `action_${step.id}_${crypto.randomUUID().slice(0, 8)}`,
    target: step.kind,
    operation: "execute",
    args: {
      description: step.description,
      planId: plan.planId,
      stepId: step.id,
    },
  }));
}

export class DefaultActionEngine implements ActionEngine {
  constructor(private readonly deps: ActionEngineDeps) {}

  async run(
    ctx: AAESContext,
    decision: AAESDecision,
  ): Promise<{ step: AAESStep; results: ActionResult[] }> {
    if (decision.blocked || !decision.selectedPlan) {
      const step = createStep("action", "skipped — decision blocked or no plan", {
        blocked: true,
      });
      step.status = "skipped";
      return { step, results: [] };
    }

    const actions = compilePlanToActions(decision.selectedPlan);
    const results: ActionResult[] = [];

    for (const action of actions) {
      const policy = this.deps.policyEngine.evaluate(ctx.request, ctx, action);
      if (!policy.allowed) {
        results.push({
          actionId: action.actionId,
          target: action.target,
          status: "denied",
          error: policy.reason,
        });
        continue;
      }

      const module = this.deps.modules.find((m) => m.canHandle(action));
      if (!module) {
        results.push({
          actionId: action.actionId,
          target: action.target,
          status: "skipped",
          error: `no module for ${action.target}`,
        });
        continue;
      }

      const result = await module.execute(action);
      results.push(result);
    }

    const step = createStep("action", `executed ${results.length} action(s)`, {
      actionIds: actions.map((a) => a.actionId),
      statuses: results.map((r) => r.status),
    });

    return { step, results };
  }
}
