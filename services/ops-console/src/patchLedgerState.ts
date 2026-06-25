import {
  type PatchLedger,
  type PatchRecord,
  seedApprovedPatches,
} from '@aaes-os/tri-core-protocol';

/** Process-wide constitutional patch ledger (seeded with three approved patches). */
const seeded = seedApprovedPatches();
export const patchLedger = seeded.ledger;

export function listPatches(): PatchRecord[] {
  return patchLedger.list();
}

export function getPatch(patchId: string): PatchRecord | undefined {
  return patchLedger.get(patchId);
}

export function proposePatch(input: {
  patchId: string;
  title: string;
  description: string;
  proposedBy: string;
}): PatchRecord {
  return patchLedger.propose(input);
}

export function approvePatch(patchId: string, approver: string): PatchRecord {
  return patchLedger.approve(patchId, approver);
}

export function rejectPatch(patchId: string): PatchRecord {
  return patchLedger.reject(patchId);
}

export function deployPatch(patchId: string): PatchRecord {
  const record = patchLedger.markDeployed(patchId);
  if (typeof globalThis !== 'undefined') {
    (globalThis as { patchLedger?: PatchLedger }).patchLedger = patchLedger;
  }
  return record;
}
