export type GovernanceDecision =
  | "approve"
  | "reject"
  | "require_fixes"
  | "escalate"
  | "freeze"
  | "retire";

export interface GovernanceReceipt {
  decisionId: string;
  corStateRef: string;
  analysisRef?: string;
  decision: GovernanceDecision;
  scope: string[];
  rationale: string;
  evidenceRefs: string[];
  invariantsEnforced: string[];
  steward: string;
  timestamp: string;
  signature: string;
}
