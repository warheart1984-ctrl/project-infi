export type UUID = string;
export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };
export interface Intent { intentId: UUID; actorId: string; type: string; payload: JsonValue; contextSnapshotId: string; createdAt: string }
export interface SubstrateStep { stepId: UUID; capability: string; substrateId: string }
export interface GovernanceProfile { id: string; riskCeiling: 'low' | 'medium' | 'high'; requiredEvidence?: string[] }
export interface PlanProvenance { islProgramId: string; islProgramVersion: string; registryRevision: string }
export interface SubstratePlan { planId: UUID; intentId: UUID; actorId: string; contextId: string; steps: SubstrateStep[]; governance: GovernanceProfile; provenance: PlanProvenance }
export interface EvidenceProvenance { intentId: UUID; substrateId: string; contentHash: string }
export interface EvidenceRecord { evidenceId: UUID; actorId: string; sourcePlanId: UUID; sourceStepId: UUID; type: string; payload: JsonValue; createdAt: string; provenance: EvidenceProvenance }
export interface StateRef { id: string; version: string; hash: string }
export interface USSUpdate { updateId: UUID; evidenceId: UUID; targetGraph: string; stateBefore: StateRef; stateAfter: StateRef; appliedAt: string }
export interface KernelStatus { ok: boolean; reasons: string[] }
