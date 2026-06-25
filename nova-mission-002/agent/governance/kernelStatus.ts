import { uuid } from "../lib/uuid";
import { getInvariants } from "./invariants";
import { getLedger } from "./ledger";
import { getSnapshots } from "../continuity/substrate";

export type KernelSubsystemStatus = "ok" | "warn" | "error";

export interface KernelStatus {
  invariantEngine: KernelSubsystemStatus;
  ledger: KernelSubsystemStatus;
  continuity: KernelSubsystemStatus;
  violationsLastMinute: number;
  receiptCount: number;
  snapshotCount: number;
  activeInvariants: number;
}

export async function kernelStatus(): Promise<KernelStatus> {
  const invariants = getInvariants();
  const ledger = getLedger();
  const snapshots = getSnapshots();

  const recentViolations = ledger.filter(
    (r) => r.blocked && Date.now() - r.timestamp < 60_000
  ).length;

  return {
    invariantEngine: invariants.length > 0 ? "ok" : "warn",
    ledger: ledger.length >= 0 ? "ok" : "error",
    continuity: snapshots.length >= 0 ? "ok" : "warn",
    violationsLastMinute: recentViolations,
    receiptCount: ledger.length,
    snapshotCount: snapshots.length,
    activeInvariants: invariants.length,
  };
}

export type KernelHeartbeat = KernelStatus & {
  kernelId: string;
  ts: number;
};

export async function emitKernelHeartbeat(): Promise<KernelHeartbeat> {
  const status = await kernelStatus();
  const hb: KernelHeartbeat = {
    ...status,
    kernelId: "crk-1",
    ts: Date.now(),
  };
  const { emitKernelHeartbeat: emitHb } = await import("../events/lifecycle");
  emitHb(hb);
  return hb;
}

export function violationId(): string {
  return uuid();
}
