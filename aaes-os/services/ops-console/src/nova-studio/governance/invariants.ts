import type { SkillzMcgeeCapability } from '../state/studioState.js';
import type { GovernanceEnvelope, GovernanceInvariant } from './receiptTypes.js';

export function evaluateGovernanceEnvelope(
  envelope: GovernanceEnvelope,
  context: { capabilities: SkillzMcgeeCapability[]; receiptCount: number },
): GovernanceInvariant[] {
  const failures: GovernanceInvariant[] = [];
  if (!envelope.inputHash.startsWith('fnv1a:')) {
    failures.push('deterministic_input_hashing');
  }
  if (!context.capabilities.some((capability) => capability.name === envelope.capability)) {
    failures.push('capability_signature_match');
  }
  const checkpointCount = Number(envelope.continuityCheckpoint.split(':').at(-1)?.replace(/\D/g, '') ?? context.receiptCount);
  if (Number.isFinite(checkpointCount) && checkpointCount > context.receiptCount) {
    failures.push('continuity_checkpoint_monotonicity');
  }
  if (!envelope.operator || !envelope.timestamp || !envelope.continuityCheckpoint) {
    failures.push('receipt_lineage_completeness');
  }
  if (envelope.status === 'ok' && !envelope.outputHash) {
    failures.push('no_orphaned_outputs');
  }
  return failures;
}
