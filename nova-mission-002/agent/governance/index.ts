export { recordReceipt, getReceipt, listReceipts } from "./receipts";
export { requireInvariant, getInvariants } from "./invariants";
export { validateAction, trace } from "./validator";
export { getLedger, getLedgerTailHash, appendToLedger } from "./ledger";
export { kernelStatus, emitKernelHeartbeat } from "./kernelStatus";
export type { KernelStatus, KernelHeartbeat } from "./kernelStatus";

import { validateAction } from "./validator";
import { recordReceipt } from "./receipts";
import { appendToLedger, getLedger, getLedgerTailHash } from "./ledger";

/** Tightened governance surface: validate, receipt, ledger.append */
export const validate = validateAction;
export const receipt = recordReceipt;
export const ledger = {
  append: appendToLedger,
  list: getLedger,
  tailHash: getLedgerTailHash,
};
