import type { GovernanceReceipt } from "./receipts";

export interface PlanStep {
  id: string;
  description: string;
  action: import("./actions").AgentAction;
}

export interface Plan {
  id: string;
  steps: PlanStep[];
  justification: string;
  receipts: GovernanceReceipt[];
}
