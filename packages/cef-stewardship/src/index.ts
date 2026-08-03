import { validateProfile, type CefProfileType } from '@aaes-os/cef-core';
import {
  evaluatePromotion,
  type CertificateDraft,
} from '@aaes-os/cef-certification';

export type StewardshipRecord = {
  certificate: CertificateDraft;
  profileValid: boolean;
  nextActions: string[];
};

/**
 * Stewardship stub: re-validates evidence and records lifecycle state.
 * Spec: docs/release/cef/STEWARDSHIP_PROTOCOL_V1.md
 */
export function stewardEvidence(
  profile: CefProfileType,
  evidence: unknown,
  evidenceRef: string,
): StewardshipRecord {
  const profileValid = validateProfile(profile, evidence).valid;
  const certificate = evaluatePromotion(profile, evidence, evidenceRef);
  const nextActions: string[] = [];

  if (!profileValid) {
    nextActions.push('fix evidence to satisfy profile schema');
  }
  if (certificate.status === 'DRAFT') {
    nextActions.push('keep certificate DRAFT until promotion gate + signature');
    nextActions.push(certificate.reason);
  }
  if (certificate.stewardshipState === 'active') {
    nextActions.push('monitor renewal_pending triggers; preserve immutability');
  }

  return { certificate, profileValid, nextActions };
}
