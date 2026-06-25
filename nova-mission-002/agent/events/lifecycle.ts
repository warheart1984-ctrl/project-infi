import type { Plan } from "../types/plan";
import type { AgentAction } from "../types/actions";
import type { GovernanceReceipt } from "../types/receipts";
import type { InvariantViolation } from "../types/invariants";

import type { KernelHeartbeat } from "../governance/kernelStatus";

type PlanListener = (plan: Plan) => void;
type ActionListener = (action: AgentAction) => void;
type ViolationListener = (violation: InvariantViolation) => void;
type ReceiptListener = (receipt: GovernanceReceipt) => void;
type KernelHeartbeatListener = (heartbeat: KernelHeartbeat) => void;

const listeners = {
  plan: [] as PlanListener[],
  action: [] as ActionListener[],
  violation: [] as ViolationListener[],
  receipt: [] as ReceiptListener[],
  kernelHeartbeat: [] as KernelHeartbeatListener[],
};

export function onPlan(cb: PlanListener): void {
  listeners.plan.push(cb);
}

export function onAction(cb: ActionListener): void {
  listeners.action.push(cb);
}

export function onViolation(cb: ViolationListener): void {
  listeners.violation.push(cb);
}

export function onReceipt(cb: ReceiptListener): void {
  listeners.receipt.push(cb);
}

export function onKernelHeartbeat(cb: KernelHeartbeatListener): void {
  listeners.kernelHeartbeat.push(cb);
}

export function emitPlan(plan: Plan): void {
  listeners.plan.forEach((cb) => cb(plan));
}

export function emitAction(action: AgentAction): void {
  listeners.action.forEach((cb) => cb(action));
}

export function emitViolation(violation: InvariantViolation): void {
  listeners.violation.forEach((cb) => cb(violation));
}

export function emitReceipt(receipt: GovernanceReceipt): void {
  listeners.receipt.forEach((cb) => cb(receipt));
}

export function emitKernelHeartbeat(heartbeat: KernelHeartbeat): void {
  listeners.kernelHeartbeat.forEach((cb) => cb(heartbeat));
}
