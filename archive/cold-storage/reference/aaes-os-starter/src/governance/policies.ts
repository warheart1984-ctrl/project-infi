import { AAESContext } from "../core/context.js"
import { PolicyResult } from "../core/types.js"

export interface PolicyEngine {
  evaluate(
    target: "plan" | "action",
    ctx: AAESContext,
    item: any
  ): Promise<PolicyResult>
}

export class DefaultPolicyEngine implements PolicyEngine {
  async evaluate(
    target: "plan" | "action",
    ctx: AAESContext,
    item: any
  ): Promise<PolicyResult> {
    return { status: "allow" }
  }
}
