/**
 * Mythic: Policy membrane
 * Engineering: DefaultPolicyEngine
 */

import type { AAESAction, AAESContext, AAESRequest, PolicyResult } from "../types.js";

const DISALLOWED_TARGETS = new Set(["filesystem", "network"]);

const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX = 30;

interface RateBucket {
  count: number;
  windowStart: number;
}

export interface PolicyEngine {
  evaluate(request: AAESRequest, ctx: AAESContext, action?: AAESAction): PolicyResult;
}

export class DefaultPolicyEngine implements PolicyEngine {
  private readonly rateLimits = new Map<string, RateBucket>();

  evaluate(request: AAESRequest, ctx: AAESContext, action?: AAESAction): PolicyResult {
    const actorId = request.actorId?.trim();
    if (!actorId) {
      return {
        allowed: false,
        reason: "actorId required for policy evaluation",
        code: "AAES_POLICY_DENIED",
      };
    }

    const rate = this.checkRateLimit(actorId);
    if (!rate.allowed) {
      return rate;
    }

    if (action) {
      const danielCheck = this.checkDanielCodeScope(action, ctx);
      if (!danielCheck.allowed) {
        return danielCheck;
      }

      const resourceCheck = this.checkResourceScope(action, ctx);
      if (!resourceCheck.allowed) {
        return resourceCheck;
      }
    }

    return { allowed: true, reason: "policy allow" };
  }

  private checkDanielCodeScope(action: AAESAction, ctx: AAESContext): PolicyResult {
    if (action.target !== "daniel.code") {
      return { allowed: true, reason: "not a daniel.code action" };
    }

    if (ctx.request.scope?.name !== "code") {
      return {
        allowed: false,
        reason: "daniel.code denied unless scope.name === 'code'",
        code: "AAES_POLICY_DENIED",
      };
    }

    return { allowed: true, reason: "daniel.code permitted in code scope" };
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

  private checkResourceScope(action: AAESAction, ctx: AAESContext): PolicyResult {
    const root = action.target.split(".")[0] ?? action.target;
    if (!DISALLOWED_TARGETS.has(root)) {
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
