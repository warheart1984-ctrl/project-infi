/**
 * Mythic: Deliberation chamber
 * Engineering: DefaultDeliberationEngine
 */

import type { AAESContext, AAESPlan, AAESStep } from "../types.js";
import { createStep } from "../types.js";

export interface DeliberationEngine {
  deliberate(ctx: AAESContext): { step: AAESStep; plans: AAESPlan[] };
}

const PLAN_PATTERNS: Record<string, (intent: string, raw: unknown) => AAESPlan> = {
  code_change: (intent, raw) => ({
    planId: `plan_code_${crypto.randomUUID().slice(0, 8)}`,
    intent,
    rationale: `Execute bounded code mutation for intent '${intent}'`,
    steps: [
      {
        id: "1",
        kind: "daniel.code",
        description: `Apply code change from normalized input: ${String(raw)}`,
      },
    ],
  }),
  analyze: (intent, raw) => ({
    planId: `plan_analyze_${crypto.randomUUID().slice(0, 8)}`,
    intent,
    rationale: "Read-only analysis pass",
    steps: [{ id: "1", kind: "analyze", description: `Inspect: ${String(raw)}` }],
  }),
  summarize: (intent, raw) => ({
    planId: `plan_summary_${crypto.randomUUID().slice(0, 8)}`,
    intent,
    rationale: "Condense payload into operator summary",
    steps: [{ id: "1", kind: "summarize", description: `Summarize: ${String(raw)}` }],
  }),
};

export class DefaultDeliberationEngine implements DeliberationEngine {
  deliberate(ctx: AAESContext): { step: AAESStep; plans: AAESPlan[] } {
    const norm = ctx.session.normalized;
    const intent = norm?.intent ?? "unknown";
    const raw = norm?.raw ?? "";
    const plans: AAESPlan[] = [];

    const primary = PLAN_PATTERNS[intent];
    if (primary) {
      plans.push(primary(intent, raw));
    } else {
      plans.push(PLAN_PATTERNS.analyze!(intent, raw));
      plans.push(PLAN_PATTERNS.summarize!(intent, raw));
    }

    if (intent !== "code_change" && plans.length < 3) {
      plans.push(PLAN_PATTERNS.summarize!(intent, raw));
    }

    const capped = plans.slice(0, 3);
    const step = createStep("deliberation", `produced ${capped.length} candidate plan(s)`, {
      planIds: capped.map((p) => p.planId),
      intent,
      raw,
    });

    return { step, plans: capped };
  }
}
