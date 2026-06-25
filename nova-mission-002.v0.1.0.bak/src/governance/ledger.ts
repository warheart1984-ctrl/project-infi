import type { GovernanceReceipt } from "../types/receipts";

const ledger: GovernanceReceipt[] = [];

export function appendToLedger(receipt: GovernanceReceipt): void {
  ledger.push(receipt);
}

export function getLedger(): readonly GovernanceReceipt[] {
  return ledger;
}

export function getLedgerTailHash(): string {
  if (ledger.length === 0) return "genesis";
  return ledger[ledger.length - 1].ledgerHash;
}

export function clearLedger(): void {
  ledger.length = 0;
}
