import { AAESContext } from "../core/context.js"
import { AAESStep } from "../core/step.js"
import { InvariantResult, Stage } from "../core/types.js"

export interface InvariantEngine {
  check(stage: Stage, ctx: AAESContext, step: AAESStep): Promise<InvariantResult>
}

export class DefaultInvariantEngine implements InvariantEngine {
  async check(
    stage: Stage,
    ctx: AAESContext,
    step: AAESStep
  ): Promise<InvariantResult> {
    if (!ctx.traceId || !ctx.request.actorId) {
      return {
        status: "block",
        messages: ["Missing traceId or actorId"]
      }
    }
    return { status: "allow" }
  }
}
