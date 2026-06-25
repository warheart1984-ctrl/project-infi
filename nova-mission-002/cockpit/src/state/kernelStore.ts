import { create } from "zustand";
import type { KernelStatus } from "../types";

export interface KernelHeartbeatPayload {
  invariantEngine: "ok" | "warn" | "error";
  constraintEngine: "ok" | "warn" | "error";
  continuity: "ok" | "warn" | "error";
  ledger: "ok" | "warn" | "error";
  pitBand: number;
  continuityAnchorHash: string;
  ledgerPrefixHash: string;
}

export interface KernelSlice {
  kernelVersion: string;
  pitBand: number;
  status: KernelStatus;
  continuityAnchorHash: string | null;
  ledgerPrefixHash: string | null;
  perAgent: Record<string, KernelHeartbeatPayload>;
}

interface KernelStoreState extends KernelSlice {
  actions: {
    setKernelVersion(version: string): void;
    setPitBand(band: number): void;
    updateStatus(status: KernelStatus): void;
    setContinuityAnchor(hash: string): void;
    updateHeartbeat(agentId: string, payload: KernelHeartbeatPayload): void;
  };
}

export const useKernelStore = create<KernelStoreState>((set) => ({
  kernelVersion: "CRK-2",
  pitBand: 1,
  status: {
    invariantEngine: "ok",
    ledger: "ok",
    continuity: "ok",
    violationsLastMinute: 0,
    receiptCount: 0,
    snapshotCount: 0,
    activeInvariants: 0,
  },
  continuityAnchorHash: null,
  ledgerPrefixHash: null,
  perAgent: {},
  actions: {
    setKernelVersion: (kernelVersion) => set({ kernelVersion }),
    setPitBand: (pitBand) => set({ pitBand }),
    updateStatus: (status) => set({ status }),
    setContinuityAnchor: (continuityAnchorHash) => set({ continuityAnchorHash }),
    updateHeartbeat: (agentId, payload) =>
      set((state) => ({
        pitBand: payload.pitBand,
        continuityAnchorHash: payload.continuityAnchorHash,
        ledgerPrefixHash: payload.ledgerPrefixHash,
        perAgent: { ...state.perAgent, [agentId]: payload },
        status: {
          ...state.status,
          invariantEngine: payload.invariantEngine,
          ledger: payload.ledger,
          continuity: payload.continuity,
        },
      })),
  },
}));
