import {
  assertPromotionAllowed,
  validateProfile,
  type CefEvidence,
  type CefProfileType,
} from '@aaes-os/cef-core';

export type CertificateStatus = 'DRAFT' | 'ACTIVE' | 'REVOKED' | 'HISTORICAL';

export type CertificateDraft = {
  certificateId: string;
  status: CertificateStatus;
  profile: CefProfileType;
  evidenceRef: string;
  promotion: CefEvidence['promotion'];
  stewardshipState: 'unpromoted' | 'active' | 'renewal_pending' | 'revoked' | 'historical';
  reason: string;
};

/**
 * Certification Engine stub: validates profile + promotion gate.
 * Does not invent signatures or flip to ACTIVE without caller-supplied authority.
 */
export function evaluatePromotion(
  profile: CefProfileType,
  evidence: unknown,
  evidenceRef: string,
): CertificateDraft {
  const profileResult = validateProfile(profile, evidence);
  const gate = assertPromotionAllowed(evidence);
  const e = evidence as CefEvidence;

  const canActivate =
    profileResult.valid &&
    gate.allowed &&
    e.promotion?.decision === 'approved' &&
    Boolean(e.promotion.signature);

  return {
    certificateId: `cert-${e.id ?? 'unknown'}`,
    status: canActivate ? 'ACTIVE' : 'DRAFT',
    profile,
    evidenceRef,
    promotion: e.promotion ?? { decision: 'hold', signature: null, timestamp: null },
    stewardshipState: canActivate ? 'active' : 'unpromoted',
    reason: canActivate
      ? 'Profile valid, promotion gate passed, signature present'
      : [
          profileResult.valid ? null : 'profile validation failed',
          gate.allowed ? null : gate.reason,
          e.promotion?.decision === 'approved' ? null : 'decision is not approved',
          e.promotion?.signature ? null : 'signature missing',
        ]
          .filter(Boolean)
          .join('; ') || 'held as DRAFT',
  };
}
