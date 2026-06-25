import { AAESContext } from "../core/context.js"
import { AAESPlan } from "../core/types.js"
import { AAESDecision } from "../core/decision.js"

export interface PlanningEngine {
  selectPlan(ctx: AAESContext, plans: AAESPlan[]): Promise<AAESDecision>
}

export class DefaultPlanningEngine implements PlanningEngine {
  async selectPlan(
    ctx: AAESContext,
    plans: AAESPlan[]
  ): Promise<AAESDecision> {
    const selected = plans[0]
    const rejected = plans.slice(1)
    return {
      decisionId: `dec_${ctx.traceId}`,
      rationale: "Default: first plan selected",
      selectedPlan: selected,
      rejectedPlans: rejected
    }
  }
}
