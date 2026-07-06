/**
 * Mythic: Planning scorer
 * Engineering: selectBestPlan
 */

import type { AAESContext, AAESDecision, AAESPlan, AAESStep } from "../types.js";
import { createStep } from "../types.js";
import { semanticCompare } from "../uls/semantic_compare.js";

export interface PlanningEngine {
  selectPlan(ctx: AAESContext, plans: AAESPlan[]): { step: AAESStep; decision: AAESDecision };
}

export function selectBestPlan(
  ctx: AAESContext,
  plans: AAESPlan[],
): { step: AAESStep; decision: AAESDecision } {
  if (plans.length === 0) {
    const decision: AAESDecision = {
      selectedPlan: null,
      rationale: "no plans available",
      blocked: true,
      blockReason: "AAES_NO_PLAN",
    };
    return {
      step: createStep("planning", "no plans to score"),
      decision,
    };
  }

  const intent = ctx.session.normalized?.intent ?? "unknown";
  const scored = plans.map((plan) => {
    let score = 0.5;
    if (plan.intent === intent) {
      score += 0.3;
    }
    const semantic = semanticCompare(plan.intent, intent);
    score += semantic * 0.1;

    if (plan.steps.some((s) => s.kind.includes("daniel.code") || s.kind.startsWith("code"))) {
      score += intent === "code_change" ? 0.2 : -0.1;
    }
    return { ...plan, score };
  });

  scored.sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
  const selected = scored[0]!;
  const rationale = `selected plan ${selected.planId} (score=${selected.score?.toFixed(2)}) — intent match for '${intent}'`;

  const decision: AAESDecision = {
    selectedPlan: selected,
    rationale,
    blocked: false,
  };

  const step = createStep("planning", rationale, {
    selectedPlanId: selected.planId,
    score: selected.score,
  });

  return { step, decision };
}

export class DefaultPlanningEngine implements PlanningEngine {
  selectPlan(ctx: AAESContext, plans: AAESPlan[]): { step: AAESStep; decision: AAESDecision } {
    return selectBestPlan(ctx, plans);
  }
}
