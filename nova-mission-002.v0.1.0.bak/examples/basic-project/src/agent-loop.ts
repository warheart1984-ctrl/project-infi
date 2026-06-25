import { nova } from "../../../src/core/agent";
import { requireInvariant } from "../../../src/governance/invariants";
import { validateAction } from "../../../src/governance/validator";
import { getContext } from "../../../src/runtime/workspace";
import { snapshot } from "../../../src/continuity/substrate";
import { onViolation, onReceipt } from "../../../src/events/lifecycle";
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

  const context = await getContext();
  const planResult = await nova.plan({ goal, context });

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
