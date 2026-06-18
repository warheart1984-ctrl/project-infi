/**
 * Mythic: Perception layer
 * Engineering: DefaultPerceptionEngine
 */

import { normalizeInput } from "../uls/normalize.js";
import type { AAESContext, AAESStep } from "../types.js";
import { createStep } from "../types.js";

export interface PerceptionEngine {
  perceive(ctx: AAESContext): AAESStep;
}

export class DefaultPerceptionEngine implements PerceptionEngine {
  perceive(ctx: AAESContext): AAESStep {
    const raw = ctx.request.payload ?? ctx.request.prompt ?? "";
    const normalized = normalizeInput(raw);
    ctx.session.normalized = normalized;
    return createStep("perception", "normalized ingress", {
      intent: normalized.intent,
      entityKeys: Object.keys(normalized.entities),
    });
  }
}
