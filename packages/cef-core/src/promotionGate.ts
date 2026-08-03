import type { CefEvidence } from './types/Evidence.js';
import { validateEvidence } from './validators/validateEvidence.js';
import { allInvariantsPassed } from './invariants.js';

export type PromotionGateResult = {
  allowed: boolean;
  reason: string;
  pendingCheckIds: string[];
};

/**
 * Claim≠evidence helper: refuse promotion.decision === "approved"
 * when any verification.check is still "pending", or schema/invariants fail.
 */
export function assertPromotionAllowed(evidence: unknown): PromotionGateResult {
  const schema = validateEvidence(evidence);
  if (!schema.valid) {
    return {
      allowed: false,
      reason: 'core schema validation failed',
      pendingCheckIds: [],
    };
  }
  if (!allInvariantsPassed(evidence)) {
    return {
      allowed: false,
      reason: 'structural invariants failed',
      pendingCheckIds: [],
    };
  }

  const e = evidence as CefEvidence;
  const checks = e.verification?.checks ?? [];
  const pendingCheckIds = checks
    .filter((c) => c.result === 'pending')
    .map((c) => c.id);

  if (e.promotion?.decision === 'approved' && pendingCheckIds.length > 0) {
    return {
      allowed: false,
      reason: `promotion approved while verification checks still pending: ${pendingCheckIds.join(', ')}`,
      pendingCheckIds,
    };
  }

  if (e.promotion?.decision === 'approved' && !e.promotion.signature) {
    return {
      allowed: false,
      reason: 'promotion approved requires non-null signature',
      pendingCheckIds,
    };
  }

  return {
    allowed: true,
    reason:
      e.promotion?.decision === 'approved'
        ? 'approved with no pending checks and signature present'
        : `decision=${e.promotion?.decision ?? 'missing'} (not an overclaim)`,
    pendingCheckIds,
  };
}

/** True when an approved decision would exceed pending verification evidence. */
export function claimExceedsEvidence(evidence: unknown): boolean {
  const e = evidence as Partial<CefEvidence>;
  if (e.promotion?.decision !== 'approved') return false;
  return !assertPromotionAllowed(evidence).allowed;
}
