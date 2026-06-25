import { AAESRequest } from "./core/request.js"
import { PerceptionEngine } from "./pipeline/perception.js"
import { DeliberationEngine } from "./pipeline/deliberation.js"
import { PlanningEngine } from "./pipeline/planning.js"
import { ActionEngine } from "./pipeline/action_engine.js"
import { InvariantEngine } from "./governance/invariants.js"
import { AuditLogger } from "./governance/audit.js"
import { AAESStep } from "./core/step.js"
import { ActionResult } from "./core/types.js"

export class AAESOrchestrator {
  constructor(
    private perception: PerceptionEngine,
    private deliberation: DeliberationEngine,
    private planning: PlanningEngine,
    private action: ActionEngine,
    private invariants: InvariantEngine,
    private audit: AuditLogger
  ) {}

  async handle(req: AAESRequest): Promise<ActionResult[]> {
    const steps: AAESStep[] = []

    const perceptionStep: AAESStep = {
      stepId: "step_perception",
      stage: "perception",
      input: req,
      output: null
    }
    const ctx = await this.perception.perceive(req)
    perceptionStep.output = ctx
    await this.invariants.check("perception", ctx, perceptionStep)
    await this.audit.logStep(ctx, perceptionStep)
    steps.push(perceptionStep)

    const deliberationStep: AAESStep = {
      stepId: "step_deliberation",
      stage: "deliberation",
      input: ctx,
      output: null
    }
    const plans = await this.deliberation.deliberate(ctx)
    deliberationStep.output = plans
    await this.invariants.check("deliberation", ctx, deliberationStep)
    await this.audit.logStep(ctx, deliberationStep)
    steps.push(deliberationStep)

    const planningStep: AAESStep = {
      stepId: "step_planning",
      stage: "planning",
      input: plans,
      output: null
    }
    const decision = await this.planning.selectPlan(ctx, plans)
    planningStep.output = decision
    await this.invariants.check("planning", ctx, planningStep)
    await this.audit.logStep(ctx, planningStep)
    steps.push(planningStep)

    const actionStep: AAESStep = {
      stepId: "step_action",
      stage: "action",
      input: decision,
      output: null
    }
    const results = await this.action.execute(ctx, decision)
    actionStep.output = results
    await this.invariants.check("action", ctx, actionStep)
    await this.audit.logStep(ctx, actionStep)
    steps.push(actionStep)

    return results
  }
}
