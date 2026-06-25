import type {
  ConstitutionalEnforcementNode,
  EnforcementReceipt,
  ProposedTransition,
} from '@aaes-os/constitutional-enforcement-node';

export type TransitionValidationStage =
  | 'pre_validation'
  | 'constitutional_validation'
  | 'commit'
  | 'block'
  | 'receipt';

export interface StructuralValidationResult {
  valid: boolean;
  stage: 'pre_validation';
  reason?: string;
}

export interface TransitionValidationResult {
  allowed: boolean;
  committed: boolean;
  stages: TransitionValidationStage[];
  receipt?: EnforcementReceipt;
  reason?: string;
}

export function validateTransition(value: unknown): StructuralValidationResult {
  if (!isRecord(value)) return invalid('transition must be an object');
  if (typeof value.transitionId !== 'string' || !value.transitionId.trim()) return invalid('transitionId is required');
  if (typeof value.transitionType !== 'string' || !value.transitionType.trim()) return invalid('transitionType is required');
  if (!Array.isArray(value.requestedCapabilities)) return invalid('requestedCapabilities must be an array');
  if (!isRecord(value.context)) return invalid('context is required');
  if (value.payload === null || typeof value.payload === 'undefined') return invalid('payload is required');
  return { valid: true, stage: 'pre_validation' };
}

export function runTransitionPipeline(
  transition: ProposedTransition,
  cen: ConstitutionalEnforcementNode,
): TransitionValidationResult {
  const structural = validateTransition(transition);
  if (!structural.valid) {
    return {
      allowed: false,
      committed: false,
      stages: ['pre_validation', 'block', 'receipt'],
      reason: structural.reason,
    };
  }

  const result = cen.execute(transition);
  return {
    allowed: result.decision.verdict === 'ALLOW',
    committed: result.committed,
    stages: [
      'pre_validation',
      'constitutional_validation',
      result.committed ? 'commit' : 'block',
      'receipt',
    ],
    receipt: result.receipt,
    reason: result.decision.reasonDetail,
  };
}

function invalid(reason: string): StructuralValidationResult {
  return { valid: false, stage: 'pre_validation', reason };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
