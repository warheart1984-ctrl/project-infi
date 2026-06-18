/**
 * Mythic: Policy membrane
 * Engineering: GovernedPolicyEngine
 */

import type { AAESAction, AAESContext, AAESRequest, PolicyResult } from "../types.js";

const FORBIDDEN_TARGETS = new Set(["filesystem", "network", "shell"]);

const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX = 30;
const MAX_ACTIONS_PER_TRACE = 50;

interface RateBucket {
  count: number;
  windowStart: number;
}

export interface PolicyEngine {
  evaluate(request: AAESRequest, ctx: AAESContext, action?: AAESAction): PolicyResult;
}

export class GovernedPolicyEngine implements PolicyEngine {
  private readonly rateLimits = new Map<string, RateBucket>();
  private readonly traceActionCounts = new Map<string, number>();

  evaluate(request: AAESRequest, ctx: AAESContext, action?: AAESAction): PolicyResult {
    const actorId = request.actorId?.trim();
    if (!actorId) {
      return {
        allowed: false,
        reason: "actorId required for policy evaluation",
        code: "AAES_POLICY_DENIED",
      };
    }

    const scopeName = request.scope?.name?.trim();
    if (!scopeName) {
      return {
        allowed: false,
        reason: "scope.name required for policy evaluation",
        code: "AAES_POLICY_DENIED",
      };
    }

    const rate = this.checkRateLimit(actorId);
    if (!rate.allowed) {
      return rate;
    }

    if (action) {
      const cap = this.checkResourceCap(ctx.traceId);
      if (!cap.allowed) {
        return cap;
      }

      const daniel = this.checkDanielCodeScope(action, scopeName);
      if (!daniel.allowed) {
        return daniel;
      }

      const forbidden = this.checkForbiddenTargets(action);
      if (!forbidden.allowed) {
        return forbidden;
      }

      const resource = this.checkResourceScope(action, ctx);
      if (!resource.allowed) {
        return resource;
      }
    }

    return { allowed: true, reason: "policy allow" };
  }

  private checkRateLimit(actorId: string): PolicyResult {
    const now = Date.now();
    let bucket = this.rateLimits.get(actorId);
    if (!bucket || now - bucket.windowStart >= RATE_LIMIT_WINDOW_MS) {
      bucket = { count: 0, windowStart: now };
      this.rateLimits.set(actorId, bucket);
    }
    bucket.count += 1;
    if (bucket.count > RATE_LIMIT_MAX) {
      return {
        allowed: false,
        reason: `rate limit exceeded for actor ${actorId}`,
        code: "AAES_POLICY_RATE_LIMIT",
      };
    }
    return { allowed: true, reason: "within rate limit" };
  }

  private checkResourceCap(traceId: string): PolicyResult {
    const count = (this.traceActionCounts.get(traceId) ?? 0) + 1;
    this.traceActionCounts.set(traceId, count);
    if (count > MAX_ACTIONS_PER_TRACE) {
      return {
        allowed: false,
        reason: `resource cap exceeded: max ${MAX_ACTIONS_PER_TRACE} actions per trace`,
        code: "AAES_POLICY_RESOURCE_CAP",
      };
    }
    return { allowed: true, reason: "within resource cap" };
  }

  /** Deny daniel.code unless scope.name === "code". */
  private checkDanielCodeScope(action: AAESAction, scopeName: string): PolicyResult {
    const fullTarget = action.target.startsWith("daniel.")
      ? action.target
      : `${action.target}.${action.operation}`;

    if (fullTarget === "daniel.code" || fullTarget.startsWith("daniel.code.")) {
      if (scopeName !== "code") {
        return {
          allowed: false,
          reason: "daniel.code denied: requires scope.name === 'code'",
          code: "AAES_POLICY_DENIED",
        };
      }
    }

    return { allowed: true, reason: "daniel scope ok" };
  }

  private checkForbiddenTargets(action: AAESAction): PolicyResult {
    const root = action.target.split(".")[0] ?? action.target;
    if (FORBIDDEN_TARGETS.has(root) || FORBIDDEN_TARGETS.has(action.target)) {
      return {
        allowed: false,
        reason: `forbidden target '${action.target}'`,
        code: "AAES_POLICY_FORBIDDEN",
      };
    }
    return { allowed: true, reason: "target not forbidden" };
  }

  private checkResourceScope(action: AAESAction, ctx: AAESContext): PolicyResult {
    const root = action.target.split(".")[0] ?? action.target;
    const sensitive = new Set(["filesystem", "network"]);
    if (!sensitive.has(root)) {
      return { allowed: true, reason: "target allowed" };
    }

    const allowed = ctx.request.scope?.resources ?? [];
    if (allowed.includes(root) || allowed.includes(action.target)) {
      return { allowed: true, reason: "target in scope.resources" };
    }

    return {
      allowed: false,
      reason: `action target '${action.target}' not permitted in scope.resources`,
      code: "AAES_POLICY_DENIED",
    };
  }
}

/** @deprecated Use GovernedPolicyEngine — alias for backward compatibility. */
export const DefaultPolicyEngine = GovernedPolicyEngine;
