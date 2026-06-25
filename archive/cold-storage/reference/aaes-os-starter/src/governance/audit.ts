import { AAESStep } from "../core/step.js"
import { AAESContext } from "../core/context.js"

export interface AuditLogger {
  logStep(ctx: AAESContext, step: AAESStep): Promise<void>
}

export class ConsoleAuditLogger implements AuditLogger {
  async logStep(ctx: AAESContext, step: AAESStep): Promise<void> {
    console.log("[AAES TRACE]", ctx.traceId, step)
  }
}
