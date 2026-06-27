export type GovernanceEnvelopeStatus = 'pending' | 'ok' | 'error';

export type GovernanceEnvelope = {
  operator: string;
  timestamp: string;
  continuityCheckpoint: string;
  capability: string;
  inputHash: string;
  outputHash?: string;
  status: GovernanceEnvelopeStatus;
};

export type GovernanceInvariant =
  | 'deterministic_input_hashing'
  | 'capability_signature_match'
  | 'continuity_checkpoint_monotonicity'
  | 'receipt_lineage_completeness'
  | 'no_orphaned_outputs';
