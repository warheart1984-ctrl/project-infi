import type { PatchProposal, TriCoreRole } from './types.js';

const SAMPLE_PATCHES: Array<Pick<PatchProposal, 'patchId' | 'description' | 'rationale' | 'proposedBy'>> = [
  {
    patchId: 'PATCH_OUTPUT_SHAPE_001',
    description: 'Normalize primitive outputs to structured objects before invariant evaluation',
    rationale: 'INV_OUTPUT_SHAPE should not fire for intentional string payloads',
    proposedBy: 'EXECUTION_CORE',
  },
  {
    patchId: 'PATCH_DETERMINISM_001',
    description: 'Sanitize timestamp and random fields before determinism invariant',
    rationale: 'Allow bounded nondeterminism in executePlan while passing governance checks',
    proposedBy: 'EXECUTION_CORE',
  },
  {
    patchId: 'PATCH_SPAN_BOUNDARY_001',
    description: 'withSpanGuard ensures spans close on thrown errors',
    rationale: 'Prevent orphan spans when executePlan fails mid-flight',
    proposedBy: 'GOVERNANCE_CORE',
  },
];

export function registerPatchProposal(
  patch: Pick<PatchProposal, 'patchId' | 'description' | 'rationale' | 'proposedBy'>,
): PatchProposal {
  const now = new Date().toISOString();
  const roles: TriCoreRole[] = ['ARCHITECTURE_CORE', 'GOVERNANCE_CORE', 'EXECUTION_CORE'];
  return {
    ...patch,
    approvals: roles.map((role) => ({ role, approved: true, timestamp: now })),
    status: 'DEPLOYED',
  };
}

export function registerSamplePatchProposals(): PatchProposal[] {
  return SAMPLE_PATCHES.map((patch) => registerPatchProposal(patch));
}
