/**
 * Mythic: Invariant gate
 * Engineering: GovernedInvariantEngine
 */

import type {
  AAESContext,
  AAESStep,
  InvariantResult,
  InvariantViolation,
} from "../types.js";

export interface InvariantEngine {
  evaluate(ctx: AAESContext, step?: AAESStep): InvariantResult;
}

export class GovernedInvariantEngine implements InvariantEngine {
  evaluate(ctx: AAESContext, step?: AAESStep): InvariantResult {
    const violations: InvariantViolation[] = [];

    violations.push(...this.checkTraceability(ctx, step));
    violations.push(...this.checkIdentity(ctx));
    violations.push(...this.checkScope(ctx));
    violations.push(...this.checkStateIntegrity(ctx));
    violations.push(...this.checkGovernanceFirst(ctx));
    violations.push(...this.checkExplainabilityHooks(ctx, step));
    violations.push(...this.checkReversibility(ctx, step));

    return {
      allowed: violations.length === 0,
      violations,
    };
  }

  /** Every step must be attributable to a trace and timestamp. */
  private checkTraceability(ctx: AAESContext, step?: AAESStep): InvariantViolation[] {
    const violations: InvariantViolation[] = [];

    if (!ctx.traceId?.trim()) {
      violations.push({
        code: "AAES_TRACE_MISSING",
        message: "traceId is required",
      });
    }

    if (step) {
      if (!step.stepId?.trim()) {
        violations.push({
          code: "AAES_TRACEABILITY",
          message: "stepId is required on pipeline steps",
        });
      }
      if (!step.timestamp?.trim()) {
        violations.push({
          code: "AAES_TRACEABILITY",
          message: "timestamp is required on pipeline steps",
        });
      }
      if (!ctx.traceId?.trim()) {
        violations.push({
          code: "AAES_TRACEABILITY",
          message: "traceId is required for traceability",
        });
      }
    }

    return violations;
  }

  /** Actor identity must be present and non-empty. */
  private checkIdentity(ctx: AAESContext): InvariantViolation[] {
    const actorId = ctx.request.actorId?.trim();
    if (!actorId) {
      return [
        {
          code: "AAES_IDENTITY_INVALID",
          message: "actorId must be non-empty",
        },
      ];
    }
    return [];
  }

  /** Scope name is mandatory for governed execution. */
  private checkScope(ctx: AAESContext): InvariantViolation[] {
    const scopeName = ctx.request.scope?.name?.trim();
    if (!scopeName) {
      return [
        {
          code: "AAES_SCOPE_MISSING",
          message: "request.scope.name is required",
        },
      ];
    }
    return [];
  }

  /** Context steps array must remain coherent (no duplicate stepIds). */
  private checkStateIntegrity(ctx: AAESContext): InvariantViolation[] {
    const seen = new Set<string>();
    for (const s of ctx.steps) {
      if (seen.has(s.stepId)) {
        return [
          {
            code: "AAES_STATE_INTEGRITY",
            message: `duplicate stepId '${s.stepId}' in context`,
          },
        ];
      }
      seen.add(s.stepId);
    }
    return [];
  }

  /** Governance metadata must not be stripped from requests. */
  private checkGovernanceFirst(ctx: AAESContext): InvariantViolation[] {
    if (ctx.request.metadata?.governanceBypass === true) {
      return [
        {
          code: "AAES_GOVERNANCE_FIRST",
          message: "governance bypass is not permitted",
        },
      ];
    }
    return [];
  }

  /** Steps should carry summary text for operator explainability. */
  private checkExplainabilityHooks(
    ctx: AAESContext,
    step?: AAESStep,
  ): InvariantViolation[] {
    if (step && !step.summary?.trim()) {
      return [
        {
          code: "AAES_EXPLAINABILITY",
          message: "step summary is required for explainability",
        },
      ];
    }
    if (ctx.steps.some((s) => !s.summary?.trim())) {
      return [
        {
          code: "AAES_EXPLAINABILITY",
          message: "all recorded steps must include a summary",
        },
      ];
    }
    return [];
  }

  /** Reversibility stub — flags irreversible step types until rollback is wired. */
  private checkReversibility(
    _ctx: AAESContext,
    step?: AAESStep,
  ): InvariantViolation[] {
    if (!step) {
      return [];
    }
    const irreversible = new Set(["destructive", "purge"]);
    if (irreversible.has(step.stepType)) {
      return [
        {
          code: "AAES_REVERSIBILITY_STUB",
          message: `step type '${step.stepType}' is not reversible in v1`,
        },
      ];
    }
    return [];
  }
}

/** @deprecated Use GovernedInvariantEngine — alias for backward compatibility. */
export const DefaultInvariantEngine = GovernedInvariantEngine;
