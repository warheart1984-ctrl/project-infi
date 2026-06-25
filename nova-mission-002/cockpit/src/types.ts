import type { Plan } from "nova-sdk";
import type { GovernanceReceipt } from "nova-sdk";
import type { Invariant, InvariantViolation } from "nova-sdk";
import type { KernelStatus } from "nova-sdk";

export type CenterMode =
  | "plan"
  | "diff"
  | "receipts"
  | "continuity"
  | "invariants"
  | "kernel"
  | "flight-deck"
  | "ledger-compare"
  | "continuity-matrix"
  | "drift";

export interface AgentLogEntry {
  id: string;
  type: "plan" | "action" | "receipt" | "violation" | "step";
  timestamp: number;
  message: string;
}

export interface ContinuityNode {
  id: string;
  timestamp: number;
  stateHash: string;
  type: "snapshot" | "receipt" | "violation";
  label?: string;
}

export interface DiffMetadata {
  action: string;
  invariantsChecked: string[];
  continuityHash: string;
  receiptId?: string;
}

export interface SelectedDiff {
  text: string;
  metadata: DiffMetadata;
}

export interface UiSignals {
  lastViolationId?: string;
  lastReceiptId?: string;
  lastPlanId?: string;
}

export type { Plan, GovernanceReceipt, Invariant, InvariantViolation, KernelStatus };
