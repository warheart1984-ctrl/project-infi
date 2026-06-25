import type { AgentAction } from "./actions";

export interface GovernanceReceipt {
  id: string;
  timestamp: number;
  action: AgentAction;
  invariantsChecked: string[];
  continuityHash: string;
  ledgerHash: string;
  blocked?: boolean;
  blockReason?: string;
}

export interface GovernanceTrace {
  receipts: GovernanceReceipt[];
  ledgerHash: string;
}
