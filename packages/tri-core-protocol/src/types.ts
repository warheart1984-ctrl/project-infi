/** Governance triad roles — distinct from Nova Face `tri_core` thalamus binding. */

export type TriCoreRole = 'ARCHITECTURE_CORE' | 'GOVERNANCE_CORE' | 'EXECUTION_CORE';

export interface PatchProposal {
  patchId: string;
  description: string;
  rationale: string;
  proposedBy: TriCoreRole;
  approvals: { role: TriCoreRole; approved: boolean; timestamp: string }[];
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'DEPLOYED';
}
