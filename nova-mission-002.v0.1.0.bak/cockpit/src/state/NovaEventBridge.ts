import { continuity, events, governance } from "nova-sdk";
import { invariants as defaultInvariants } from "../../../config/nova.config";
import { useKernelStore } from "./kernelStore";
import { useCockpitState } from "./store";

let initialized = false;
let heartbeatTimer: ReturnType<typeof setInterval> | null = null;

export async function initializeNovaEventBridge(): Promise<void> {
  if (initialized) return;
  initialized = true;

  const actions = useCockpitState.getState().actions;

  for (const inv of defaultInvariants) {
    await governance.requireInvariant(inv);
  }
  actions.setInvariants([...defaultInvariants]);

  events.onPlan((plan) => {
    actions.setPlan(plan);
    actions.signalPlan(plan.id);
    actions.appendLog({
      type: "plan",
      timestamp: Date.now(),
      message: `Plan generated (${plan.steps.length} steps)`,
    });
    setTimeout(() => actions.clearSignal("lastPlanId"), 800);
  });

  events.onAction((action) => {
    actions.appendLog({
      type: "action",
      timestamp: Date.now(),
      message: `Action: ${action.type}`,
    });
  });

  events.onReceipt((receipt) => {
    actions.addReceipt(receipt);
    actions.signalReceipt(receipt.id);
    actions.appendLog({
      type: "receipt",
      timestamp: Date.now(),
      message: `Receipt ${receipt.id.slice(0, 8)}… emitted`,
    });
    void continuity.snapshot().then((snapshot) => {
      actions.updateContinuity(snapshot);
    });
    setTimeout(() => actions.clearSignal("lastReceiptId"), 800);
  });

  events.onViolation((violation) => {
    actions.addViolation(violation);
    actions.signalViolation(violation.id);
    actions.appendLog({
      type: "violation",
      timestamp: Date.now(),
      message: `Invariant violated: ${violation.invariantId}`,
    });
    setTimeout(() => actions.clearSignal("lastViolationId"), 600);
  });

  events.onKernelHeartbeat((hb) => {
    actions.updateKernelStatus(hb);
    useKernelStore.getState().actions.updateStatus(hb);
  });

  const poll = async () => {
    const status = await governance.kernelStatus();
    actions.updateKernelStatus(status);
    await governance.emitKernelHeartbeat();
  };

  await poll();
  heartbeatTimer = setInterval(() => void poll(), 2000);
}

export function teardownNovaEventBridge(): void {
  if (heartbeatTimer) clearInterval(heartbeatTimer);
  initialized = false;
}
