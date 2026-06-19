import { PatchLedger } from './patchLedger.js';
import { PatchProvenanceChain } from './patchProvenance.js';

export interface SeedPatchesResult {
  ledger: PatchLedger;
  provenance: PatchProvenanceChain;
}

/** Seed the three constitutional patches (Daniel proposes, Dar-z + Jon approve, deploy). */
export function seedApprovedPatches(): SeedPatchesResult {
  const ledger = new PatchLedger();
  const provenance = new PatchProvenanceChain();

  const patches = [
    {
      patchId: 'PATCH_OUTPUT_SHAPE_001',
      title: 'Output Shape Normalizer',
      description: 'Wrap non-object outputs in a structured envelope before invariant checks.',
      proposedBy: 'EXECUTION_CORE',
    },
    {
      patchId: 'PATCH_DETERMINISM_001',
      title: 'Determinism Sanitizer',
      description: 'Strip random and timestamp fields from outputs before determinism invariant.',
      proposedBy: 'EXECUTION_CORE',
    },
    {
      patchId: 'PATCH_SPAN_BOUNDARY_001',
      title: 'Span Boundary Guard',
      description: 'Guarantee span close in a finally block around runtime execution.',
      proposedBy: 'EXECUTION_CORE',
    },
  ] as const;

  for (const patch of patches) {
    ledger.propose(patch);
    provenance.append({
      patchId: patch.patchId,
      action: 'PROPOSED',
      actor: 'EXECUTION_CORE',
      timestamp: new Date().toISOString(),
    });

    for (const approver of ['GOVERNANCE', 'ARCHITECTURE'] as const) {
      ledger.approve(patch.patchId, approver);
      provenance.append({
        patchId: patch.patchId,
        action: 'APPROVED',
        actor: approver,
        timestamp: new Date().toISOString(),
      });
    }

    ledger.markDeployed(patch.patchId);
    provenance.append({
      patchId: patch.patchId,
      action: 'DEPLOYED',
      actor: 'GOVERNANCE',
      timestamp: new Date().toISOString(),
    });
  }

  globalThis.patchLedger = ledger;
  globalThis.patchProvenance = provenance;

  return { ledger, provenance };
}

export function clearPatchGlobals(): void {
  globalThis.patchLedger = undefined;
  globalThis.patchProvenance = undefined;
}

declare global {
  // eslint-disable-next-line no-var
  var patchProvenance: PatchProvenanceChain | undefined;
}
