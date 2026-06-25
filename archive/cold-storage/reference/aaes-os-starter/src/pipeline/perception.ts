import { AAESRequest } from "../core/request.js"
import { AAESContext } from "../core/context.js"
import { PolicySet } from "../core/types.js"

export interface PerceptionEngine {
  perceive(req: AAESRequest): Promise<AAESContext>
}

export class DefaultPerceptionEngine implements PerceptionEngine {
  async perceive(req: AAESRequest): Promise<AAESContext> {
    const traceId = `trace_${req.id}`
    const policies: PolicySet = { name: "default", rules: [] }
    return {
      request: req,
      traceId,
      session: {},
      policies
    }
  }
}
