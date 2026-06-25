import { AAESContext } from "../core/context.js"
import { AAESDecision } from "../core/decision.js"
import { ActionResult } from "../core/types.js"
import { AAESAction } from "../core/action.js"
import { ExecutionModule } from "../modules/registry.js"

export interface ActionEngine {
  execute(ctx: AAESContext, decision: AAESDecision): Promise<ActionResult[]>
}

export class DefaultActionEngine implements ActionEngine {
  constructor(private modules: ExecutionModule[]) {}

  async execute(
    ctx: AAESContext,
    decision: AAESDecision
  ): Promise<ActionResult[]> {
    const actions: AAESAction[] = [] // TODO: derive from plan
    const results: ActionResult[] = []

    for (const action of actions) {
      const mod = this.modules.find(m => m.canHandle(action))
      if (!mod) {
        results.push({
          actionId: action.actionId,
          status: "failed",
          details: "No module can handle action"
        })
        continue
      }
      const res = await mod.execute(action, ctx)
      results.push(res)
    }

    return results
  }
}
