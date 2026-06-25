import { sha256Sync } from "../lib/hash";
import { uuid } from "../lib/uuid";
import type { AgentAction } from "../types/actions";
import type { GovernanceReceipt } from "../types/receipts";
import { getContinuityHash } from "../continuity/substrate";
import { appendToLedger, getLedgerTailHash } from "./ledger";

export async function recordReceipt(
  action: AgentAction,
  invariantsChecked: string[],
  options?: { blocked?: boolean; blockReason?: string }
): Promise<GovernanceReceipt> {
  const continuityHash = await getContinuityHash();
  const prevHash = getLedgerTailHash();

  const receipt: GovernanceReceipt = {
    id: uuid(),
    timestamp: Date.now(),
    action,
    invariantsChecked,
    continuityHash,
    ledgerHash: "",
    blocked: options?.blocked,
    blockReason: options?.blockReason,
  };

  receipt.ledgerHash = sha256Sync(JSON.stringify(receipt) + prevHash);

  appendToLedger(receipt);
  return receipt;
}

export async function getReceipt(id: string): Promise<GovernanceReceipt | null> {
  const { getLedger } = await import("./ledger");
  return getLedger().find((r) => r.id === id) ?? null;
}

export async function listReceipts(): Promise<GovernanceReceipt[]> {
  const { getLedger } = await import("./ledger");
  return [...getLedger()];
}
