import crypto from "node:crypto";
import type { GovernanceReceipt } from "../types/governance.js";

export function signReceiptPayload(receipt: Omit<GovernanceReceipt, "signature">): string {
  const payload = JSON.stringify({
    decisionId: receipt.decisionId,
    corStateRef: receipt.corStateRef,
    decision: receipt.decision,
    scope: receipt.scope,
    rationale: receipt.rationale,
    steward: receipt.steward,
    timestamp: receipt.timestamp,
  });
  return crypto.createHash("sha256").update(payload, "utf8").digest("hex");
}
