import type { Fault, Receipt, RunContext } from '../types.js';
import type { InvariantResult } from '../governance/types.js';

export interface RunLedgerStore {
  recordReceipt(ctx: RunContext, result: unknown): Promise<Receipt>;
  recordFault(ctx: RunContext, fault: InvariantResult): Promise<Fault>;
  getReceipt(runId: string): Receipt | undefined;
  getFault(runId: string): Fault | undefined;
  listReceipts(): Receipt[];
  listFaults(): Fault[];
}
