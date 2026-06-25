import { AAESContext } from "../core/context.js"
import { AAESPlan } from "../core/types.js"

export interface DeliberationEngine {
  deliberate(ctx: AAESContext): Promise<AAESPlan[]>
}

export class DefaultDeliberationEngine implements DeliberationEngine {
  async deliberate(ctx: AAESContext): Promise<AAESPlan[]> {
    return [
      {
        id: "plan_1",
        description: "Default single-step plan",
        steps: []
      }
    ]
  }
}
