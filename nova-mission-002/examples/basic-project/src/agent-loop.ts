import { AgentRuntime } from "../../../agent";
import { requireInvariant } from "../../../agent/governance/invariants";
import { validateAction } from "../../../agent/governance/validator";
import { getContext } from "../../../agent/runtime/workspace";
import { snapshot } from "../../../agent/continuity/substrate";
import { onViolation, onReceipt } from "../../../agent/events/lifecycle";
import { invariants } from "./nova.config";

async function setupGovernance() {
  for (const inv of invariants) {
    await requireInvariant(inv);
  }

  onViolation((v) => {
    console.error("Invariant violation:", v.invariantId, v.description);
  });

  onReceipt((r) => {
    console.log("Receipt:", r.id, r.continuityHash);
  });
}

async function runAgent(goal: string) {
  await setupGovernance();

  const runtime = new AgentRuntime();
  const context = await getContext();
  const planResult = await runtime.plan({ goal, context });

  console.log("Plan:", planResult.plan.justification);
  console.log("Steps:", planResult.plan.steps.length);

  for (const step of planResult.plan.steps) {
    const validation = await validateAction(step.action);
    if (!validation.ok) {
      console.error("Blocked step:", validation.reason);
      break;
    }

    console.log("Executing step:", step.description);
    const snap = await snapshot();
    console.log("Snapshot:", snap.id);
  }
}

runAgent("Refactor the data access layer for clarity and testability.").catch(console.error);
