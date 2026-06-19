export * from './patchProposals.js';
export * from './types.js';

export {
  PatchLedger,
  type PatchRecord,
  type PatchStatus,
} from './patchLedger.js';

export {
  PatchProvenanceChain,
  type ProvenanceEntry,
} from './patchProvenance.js';

export {
  PATCH_OUTPUT_SHAPE_001,
  PATCH_DETERMINISM_001,
  PATCH_SPAN_BOUNDARY_001,
  applyDeployedOutputPatches,
  applyOutputShapePatch,
  sanitizeDeterminism,
  withSpanGuard,
  getPatchLedger,
  isPatchDeployed,
} from './patchApply.js';

export {
  seedApprovedPatches,
  clearPatchGlobals,
  type SeedPatchesResult,
} from './seedPatches.js';
