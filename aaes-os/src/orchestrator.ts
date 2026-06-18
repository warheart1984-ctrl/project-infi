/**
 * Mythic: Cognitive orchestrator
 * Engineering: AAESOrchestrator
 */

import type { ActionEngine } from "./pipeline/action_engine.js";
import type { DeliberationEngine } from "./pipeline/deliberation.js";
import type { InvariantEngine } from "./engines/invariant_engine.js";
import type { PerceptionEngine } from "./pipeline/perception.js";
import type { PlanningEngine } from "./pipeline/planning.js";
import type {
  AAESContext,
  AAESRequest,
  AAESStep,
  AuditLogger,
  OrchestratorResult,
} from "./types.js";
import { createStep, newTraceId } from "./types.js";

export interface OrchestratorDeps {
  invariantEngine: InvariantEngine;
  perceptionEngine: PerceptionEngine;
  deliberationEngine: DeliberationEngine;
  planningEngine: PlanningEngine;
  actionEngine: ActionEngine;
  auditLogger: AuditLogger;
}

export class AAESOrchestrator {
  constructor(private readonly deps: OrchestratorDeps) {}

  async handle(request: AAESRequest): Promise<OrchestratorResult> {
    const traceId = request.traceId?.trim() || newTraceId();
    const ctx: AAESContext = {
      traceId,
      request,
      session: {},
      steps: [],
      metadata: {},
    };

    const ingress = createStep("ingress", "request admitted", {
      actorId: request.actorId,
      scope: request.scope?.name,
    });

    const ingressInvariant = this.deps.invariantEngine.evaluate(ctx, ingress);
    if (!ingressInvariant.allowed) {
      return this.blocked(
        ctx,
        ingress,
        ingressInvariant.violations[0]?.code ?? "AAES_INVARIANT_BLOCK",
        ingressInvariant.violations.map((v) => v.message).join("; "),
      );
    }

    this.record(ctx, ingress);

    const perceptionStep = this.deps.perceptionEngine.perceive(ctx);
    const perceptionInvariant = this.deps.invariantEngine.evaluate(ctx, perceptionStep);
    if (!perceptionInvariant.allowed) {
      return this.blocked(
        ctx,
        perceptionStep,
        "AAES_INVARIANT_BLOCK",
        perceptionInvariant.violations.map((v) => v.message).join("; "),
      );
    }
    this.record(ctx, perceptionStep);

    const { step: deliberationStep, plans } = this.deps.deliberationEngine.deliberate(ctx);
    this.record(ctx, deliberationStep);

    const { step: planningStep, decision } = this.deps.planningEngine.selectPlan(ctx, plans);
    this.record(ctx, planningStep);

    if (decision.blocked) {
      planningStep.status = "blocked";
      return {
        ok: false,
        traceId,
        results: [],
        decision,
        steps: ctx.steps,
        error: {
          code: decision.blockReason ?? "AAES_DECISION_BLOCKED",
          message: decision.rationale,
        },
      };
    }

    const { step: actionStep, results } = await this.deps.actionEngine.run(ctx, decision);
    this.record(ctx, actionStep);

    const complete = createStep("complete", "orchestration finished", {
      resultCount: results.length,
    });
    this.record(ctx, complete);

    return {
      ok: true,
      traceId,
      results,
      decision,
      steps: ctx.steps,
    };
  }

  private record(ctx: AAESContext, step: AAESStep): void {
    ctx.steps.push(step);
    this.deps.auditLogger.appendStep(ctx, step);
  }

  private blocked(
    ctx: AAESContext,
    step: AAESStep,
    code: string,
    message: string,
  ): OrchestratorResult {
    step.status = "blocked";
    this.record(ctx, step);
    return {
      ok: false,
      traceId: ctx.traceId,
      results: [],
      steps: ctx.steps,
      error: { code, message },
    };
  }
}

/** @deprecated Use AAESOrchestrator */
export { AAESOrchestrator as AaesOsOrchestrator };
