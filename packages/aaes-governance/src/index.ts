export {
  FAULT_CODE_AUTHORITY_MISMATCH,
  FAULT_CODE_BRIDGE_BINDING_MISMATCH,
  FAULT_CODE_INVARIANT_BREACH,
  FAULT_CODE_RUNTIME_TIMEOUT,
  FAULT_CODE_SPAN_ORPHAN,
  FAULT_CODES,
  type FaultCode,
} from './faultCodes.js';

export {
  asFaultId,
  type FaultEvent,
  type RecordFaultInput,
  type FaultId,
  type Severity,
} from './faultTypes.js';

export { FaultJournal } from './faultJournal.js';
export { DriftMetrics, type DriftScore } from './driftMetrics.js';
export { PatternLedger, type PatternRecord } from './patternLedger.js';
export { PatchAnalytics, type PatchEffectivenessRecord } from './patchAnalytics.js';

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
} from './invariantEngine.js';

export { OutputShapeInvariant } from './invariants/outputShape.js';
export { DeterminismInvariant } from './invariants/determinism.js';
export {
  type GovernanceTraceBus,
  type GovernanceTraceEvent,
  type FaultTraceEvent,
  type InvariantTraceEvent,
} from './tracePort.js';

export { initGovernanceGlobals, recordFaultWithPattern } from './bootstrap.js';
export { collectTelemetrySnapshot, type TelemetrySnapshot } from './telemetry.js';
