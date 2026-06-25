import { createHash } from "crypto";

export interface ReceiptV2 {
  id: string;
  actionId: string;
  invariantsChecked: string[];
  continuityHash: string;
  prevHash: string;
  hash: string;
  annotations?: { author: string; note: string }[];
}

const ledger: ReceiptV2[] = [];

export function appendReceipt(
  receipt: Omit<ReceiptV2, "prevHash" | "hash">
): ReceiptV2 {
  const last = ledger[ledger.length - 1];
  const prevHash = last?.hash ?? "genesis";
  const hash = createHash("sha256")
    .update(prevHash + JSON.stringify(receipt))
    .digest("hex");
  const full: ReceiptV2 = { ...receipt, prevHash, hash };
  ledger.push(full);
  return full;
}

export function listReceipts(): ReceiptV2[] {
  return [...ledger];
}
