import type { Plan, PlanStep } from "../types/plan";
import type { PlanInput } from "../types/actions";
import { uuid } from "../lib/uuid";
import { recordReceipt } from "../governance/receipts";
import { validateAction } from "../governance/validator";
import { emitPlan } from "../events/lifecycle";

export async function plan(input: PlanInput): Promise<{ plan: Plan; receipts: import("../types/receipts").GovernanceReceipt[] }> {
  const action = { type: "plan" as const, payload: { goal: input.goal, context: input.context } };

  const validation = await validateAction(action);
  if (!validation.ok) {
    await recordReceipt(action, [], { blocked: true, blockReason: validation.reason });
    throw new Error(validation.reason ?? "Plan blocked by invariant");
  }

  const steps: PlanStep[] = [
    {
      id: uuid(),
      description: `Analyze workspace for: ${input.goal}`,
      action: { type: "run", payload: { command: "analyze" } },
    },
    {
      id: uuid(),
      description: `Propose changes for: ${input.goal}`,
      action: { type: "edit", payload: { goal: input.goal } },
    },
    {
      id: uuid(),
      description: "Verify with invariants and tests",
      action: { type: "run", payload: { command: "verify" } },
    },
  ];

  const planReceipt = await recordReceipt(action, validation.ok ? ["plan-validated"] : []);
  const planObj: Plan = {
    id: uuid(),
    steps,
    justification: `Governed plan for: ${input.goal}`,
    receipts: [planReceipt],
  };

  emitPlan(planObj);
  return { plan: planObj, receipts: [planReceipt] };
}
