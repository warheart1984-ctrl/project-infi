/**
 * Simplified Receipt v2 models (Article XIII) — TypeScript mirror of receipts/models.py
 */

export type ReceiptKind =
  | "Decision"
  | "Observation"
  | "Divergence"
  | "Arbitration"
  | "Remediation"
  | "Closure";

export interface SixDimensionContract {
  invariant: string;
  evidenceIds: string[];
  authorityChain: string[];
  reproducible: boolean;
  impactBoundary: string;
  accountableParty: string;
}

export interface ReceiptV2 {
  receiptId: string;
  kind: ReceiptKind;
  runtime: string;
  stateObjectId: string;
  stateType: string;
  contract: SixDimensionContract;
  timestamp: string;
  lifecyclePrev?: ReceiptKind;
  lifecycleNext?: ReceiptKind;
  payload: Record<string, unknown>;
}

export interface TruthPayload {
  claimId: string;
  claimText: string;
  verdict: "supported" | "verified" | "rejected" | "uncertain";
  confidence: number;
  evidenceBundleId: string;
}

export interface TruthReceipt extends ReceiptV2 {
  runtime: "TruthVerificationRuntime";
  payload: TruthPayload;
}

export interface SovereigntyPayload {
  grantId: string;
  subjectId: string;
  authorityScope: string;
  delegationChain: string[];
  status: "delegated" | "active" | "suspended" | "revoked";
}

export interface SovereigntyReceipt extends ReceiptV2 {
  runtime: "SovereigntyRuntime";
  payload: SovereigntyPayload;
}

export interface ReproductionPayload {
  originalReceiptId: string;
  reproductionRunId: string;
  matched: boolean;
  divergenceSummary?: string;
  divergenceFields: string[];
}

export interface ReproductionReceipt extends ReceiptV2 {
  runtime: "ReproductionRuntime";
  payload: ReproductionPayload;
}

export const RECEIPT_LIFECYCLE_GRAPH: Record<ReceiptKind, ReceiptKind[]> = {
  Decision: ["Observation"],
  Observation: ["Divergence", "Closure"],
  Divergence: ["Arbitration", "Remediation"],
  Arbitration: ["Remediation", "Closure"],
  Remediation: ["Closure"],
  Closure: [],
};
