export {
  FAULT_CODE_AUTHORITY_MISMATCH,
  FAULT_CODE_BRIDGE_BINDING_MISMATCH,
  FAULT_CODE_INVARIANT_BREACH,
  FAULT_CODE_RUNTIME_TIMEOUT,
  FAULT_CODE_SPAN_ORPHAN,
  FAULT_CODES,
  type FaultCode,
} from './faultCodes.js';

export { type GovernanceContext, type GovernanceActor } from './context/GovernanceContext.js';

export { FaultJournalStore, type FaultJournalStoreOptions, type FaultRecord, type FaultRecordInput } from './faults/FaultJournalStore.js';
export { constitutionalProfile, type ConstitutionalProfile } from './constitutionalProfile.js';
export {
  deriveCanonicalReplayEvidenceContract,
  type CanonicalReplayEvidenceContract,
  type ReplayVerificationReport,
  validateCanonicalReplayEvidenceContract,
  verifyReplayCoverage,
} from './crec.js';
export {
  CONSTITUTIONAL_EVIDENCE_GRAPH_JSON_SCHEMA,
  CONSTITUTIONAL_EVIDENCE_GRAPH_JSON_SCHEMA_VERSION,
  createConstitutionalEvidenceGraph,
  createConstitutionalEvidenceGraphFromProofSurfaces,
  type ConstitutionalEvidenceGraph,
  type ConstitutionalEvidenceGraphClaimResolution,
  type ConstitutionalEvidenceGraphEdge,
  type ConstitutionalEvidenceGraphEdgeRelation,
  type ConstitutionalEvidenceGraphNode,
  type ConstitutionalEvidenceGraphNodeKind,
  type ConstitutionalEvidenceGraphNodeStatus,
  type ConstitutionalEvidenceGraphProofSurface,
  type ConstitutionalEvidenceGraphSource,
  type ConstitutionalEvidenceGraphSummary,
  type ConstitutionalEvidenceGraphView,
  type ConstitutionalEvidenceGraphValidationIssue,
  type ConstitutionalReleaseReceipt,
  resolveConstitutionalEvidenceGraph,
  resolveConstitutionalEvidenceGraphFromProofSurfaces,
  resolveConstitutionalEvidenceGraphFromReleaseReceipt,
  summarizeConstitutionalEvidenceGraph,
  validateConstitutionalEvidenceGraph,
} from './evidenceGraph.js';
export {
  PROOF_SURFACE_LAW,
  type ClaimType,
  type ProofLevel,
  type ProofSurface,
  type ProofSurfaceArtifactType,
  type ProofSurfaceCommercialReadiness,
  type ProofSurfaceConstitutionalProfile,
  type ProofSurfaceEvidence,
  type ProofSurfaceIdentity,
  type ProofSurfaceOperationalStatus,
  type ProofSurfaceReadiness,
  type ProofSurfaceReplayStatus,
  type ProofSurfaceValidationIssue,
  type ProofSurfaceValidationResult,
  type ProofSurfaceVerificationStatus,
  ProofSurfaceRegistry,
  createProofSurface,
  deriveProofLevel,
  minProofLevelForClaimType,
  validateProofSurface,
} from './proofSurface.js';
export {
  type ProofSurfaceCatalogDocument,
  type ProofSurfaceDocument,
  type ProofSurfaceSnapshot,
} from './proofSurfaceJson.js';
export { createDemoProofSurfaceRegistry, type ProofSurfaceSummary, listProofSurfaceSummaries } from './proofSurfaceCatalog.js';
export {
  createProofSurfaceDocument,
  createProofSurfaceCatalogDocument,
  parseProofSurfaceDocument,
  PROOF_SURFACE_CATALOG_JSON_SCHEMA,
  PROOF_SURFACE_JSON_SCHEMA,
  PROOF_SURFACE_JSON_SCHEMA_VERSION,
  serializeProofSurfaceCatalog,
  serializeProofSurfaceDocument,
  snapshotProofSurface,
} from './proofSurfaceJson.js';

export {
  asFaultId,
  type FaultEvent,
  type RecordFaultInput,
  type FaultId,
  type Severity,
} from './faultTypes.js';

export { FaultJournal } from './faultJournal.js';
export { DriftMetrics, type DriftScore } from './driftMetrics.js';
export {
  PatternLedger,
  type PatternLedgerEntry,
  type PatternLedgerEntryInput,
  type PatternRecord,
} from './patternLedger.js';
export { type VerdictClass } from './verdict.js';
export { PatchAnalytics, type PatchEffectivenessRecord } from './patchAnalytics.js';

export { type LedgerActor, type LedgerEntry, type LedgerEntryInput, LEDGER_GENESIS_HASH } from './ledger/LedgerEntry.js';
export { RunLedger, type RunLedgerOptions } from './ledger/RunLedger.js';

export {
  GovernanceHub,
  createMinimalInvariantEngine,
  countInvariantFaults,
  countSpanBoundaryFaults,
  syncPatternsFromJournal,
  type GovernanceHubOptions,
} from './governanceHub.js';

export {
  InvariantEngine,
  type Invariant,
  type InvariantContext,
  type InvariantResult,
  type InvariantSeverity,
  evaluateInvariant,
  registerCoreInvariants,
  registerGovernanceInvariants,
} from './invariantEngine.js';

export { OutputShapeInvariant } from './invariants/outputShape.js';
export { DeterminismInvariant } from './invariants/determinism.js';
export { coreInvariants } from './invariants/coreInvariants.js';
export { TriCoreProtocol } from './tricore/TriCoreProtocol.js';
export {
  type TriCoreActor,
  type TriCoreKnownMessageType,
  type TriCoreMessageInput,
  type TriCoreRoutingDecision,
} from './tricore/messages.js';
export { GovernanceLoop } from './loop/GovernanceLoop.js';
export { ConstitutionalFreeze, type ConstitutionalFreezeState } from './freeze/ConstitutionalFreeze.js';
export {
  freezeInvariant,
  freezeInvariants,
  registerFreezeInvariants,
} from './freeze/FreezeInvariant.js';
export { SubstrateBridge, type SubstrateBridgeOptions, isSubstrateSignalPayload } from './substrate/SubstrateBridge.js';
export { type SubstrateSignal } from './substrate/SubstrateSignal.js';
export {
  substrateInvariants,
  registerSubstrateInvariants,
} from './substrate/SubstrateInvariants.js';
export {
  type GovernanceTraceBus,
  type GovernanceTraceEvent,
  type FaultTraceEvent,
  type InvariantTraceEvent,
} from './tracePort.js';

export { initGovernanceGlobals, recordFaultWithPattern } from './bootstrap.js';
export { collectTelemetrySnapshot, type TelemetrySnapshot } from './telemetry.js';

export {
  type ActorKind,
  type TriCoreMessageBase,
  type GovernanceToRuntime,
  type RuntimeToAgent,
  type AgentToRuntime,
  type RuntimeToGovernance,
  type AgentToGovernance,
  type TriCoreMessage,
  type TriCoreBus,
  InMemoryTriCoreBus,
} from './tricore.js';
