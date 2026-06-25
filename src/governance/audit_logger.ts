/**
 * Mythic: Audit chronicle
 * Engineering: ConsoleAuditLogger
 */

import type { AAESContext, AAESStep, AuditLogger } from "../types.js";
import type { TraceStore } from "../storage/trace_store.js";

export class ConsoleAuditLogger implements AuditLogger {
  constructor(private readonly traceStore?: TraceStore) {}

  appendStep(ctx: AAESContext, step: AAESStep): void {
    console.log(
      JSON.stringify({
        type: "aaes_audit",
        traceId: ctx.traceId,
        stepId: step.stepId,
        stepType: step.stepType,
        summary: step.summary,
        status: step.status,
      }),
    );
    this.traceStore?.appendStep(ctx, step);
  }
}

export class TraceStoreAuditLogger implements AuditLogger {
  constructor(private readonly store: TraceStore) {}

  appendStep(ctx: AAESContext, step: AAESStep): void {
    this.store.appendStep(ctx, step);
  }
}

export class CompositeAuditLogger implements AuditLogger {
  constructor(private readonly loggers: AuditLogger[]) {}

  appendStep(ctx: AAESContext, step: AAESStep): void {
    for (const logger of this.loggers) {
      logger.appendStep(ctx, step);
    }
  }
}
