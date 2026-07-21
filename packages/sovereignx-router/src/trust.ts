import crypto from 'node:crypto';

import type { RelationshipLedgerTrustPacket, RelationshipTrustView, TrustBand } from './types.js';
import {
  type CandidateModel,
  type DelegationLink,
  type RetirementPolicy,
  type TrustAuditPacket,
  type TrustHeuristics,
  applyTrustToCandidateModel,
  buildTrustAuditPacket,
  canPromote,
  computeTrustScore,
  decayedTrustScore,
  deriveAuthorityLevel,
  inheritedTrustScore,
  resolveTrustConflict,
  shouldRetireModel,
  trustBand,
  TRUST_GOVERNANCE_TIERS,
} from './routingDsl.js';

export type {
  CandidateModel,
  DelegationLink,
  RelationshipLedgerTrustPacket,
  RelationshipTrustView,
  RetirementPolicy,
  TrustAuditPacket,
  TrustBand,
  TrustHeuristics,
};
export {
  applyTrustToCandidateModel,
  buildTrustAuditPacket,
  canPromote,
  computeTrustScore,
  decayedTrustScore,
  deriveAuthorityLevel,
  inheritedTrustScore,
  resolveTrustConflict,
  shouldRetireModel,
  trustBand,
  TRUST_GOVERNANCE_TIERS,
};

export interface SignedRelationshipTrustPacket {
  algorithm: 'HMAC-SHA256';
  signer: string;
  signedAt: string;
  value: string;
}

export function signRelationshipTrustPacket(
  packet: RelationshipLedgerTrustPacket,
  secret: string,
  signer = 'sovereignx-router',
  signedAt = new Date().toISOString(),
): SignedRelationshipTrustPacket {
  const value = crypto.createHmac('sha256', secret).update(canonicalizeJson(packet)).digest('hex');
  return {
    algorithm: 'HMAC-SHA256',
    signer,
    signedAt,
    value,
  };
}

export function verifyRelationshipTrustPacket(
  packet: RelationshipLedgerTrustPacket,
  signature: SignedRelationshipTrustPacket | undefined,
  secret: string,
): boolean {
  if (!signature || signature.algorithm !== 'HMAC-SHA256') {
    return false;
  }
  const expected = signRelationshipTrustPacket(packet, secret, signature.signer, signature.signedAt).value;
  return expected === signature.value;
}

export type GovernanceTrustLevel = 'basic' | 'enhanced' | 'full';

export interface GovernanceTrustPolicy extends TrustHeuristics {
  governanceLevel: GovernanceTrustLevel;
}

export const GOVERNANCE_TRUST_POLICIES: Record<GovernanceTrustLevel, GovernanceTrustPolicy> = {
  basic: {
    governanceLevel: 'basic',
    minTrustScore: 0.2,
    minTrustBand: 'low',
    preferHighTrustBand: false,
  },
  enhanced: {
    governanceLevel: 'enhanced',
    minTrustScore: 0.55,
    minTrustBand: 'medium',
    preferHighTrustBand: false,
  },
  full: {
    governanceLevel: 'full',
    minTrustScore: 0.75,
    minTrustBand: 'high',
    preferHighTrustBand: true,
  },
};

export interface PromotionRequest {
  requestId: string;
  orgId: string;
  artifactId: string;
  evidenceIds: string[];
  provenance: {
    originSystem: string;
    originActorId?: string;
    method: string;
    standardsTraceabilityIds?: string[];
  };
  governanceLevel: string;
  trust: RelationshipTrustView;
}

export function trustPolicyForGovernanceLevel(governanceLevel: string | undefined | null): GovernanceTrustPolicy {
  if (governanceLevel === 'basic' || governanceLevel === 'enhanced' || governanceLevel === 'full') {
    return GOVERNANCE_TRUST_POLICIES[governanceLevel];
  }
  return GOVERNANCE_TRUST_POLICIES.basic;
}

export function relationshipTrustFromPacket(packet: RelationshipLedgerTrustPacket | null | undefined): RelationshipTrustView | undefined {
  if (!packet) {
    return undefined;
  }

  return {
    score: packet.trust.score,
    band: packet.trust.band,
    evidenceIds: [...packet.trust.evidenceIds],
    authority: packet.trust.authority ? { ...packet.trust.authority } : undefined,
    provenance: packet.trust.provenance ? { ...packet.trust.provenance } : undefined,
  };
}

export function promoteWithTrustGate(
  request: PromotionRequest,
  heuristics: TrustHeuristics = trustPolicyForGovernanceLevel(request.governanceLevel),
): { allowed: boolean; reason: string } {
  const allowed = canPromote(request.trust.score, request.trust.band, heuristics);
  return {
    allowed,
    reason: allowed
      ? 'promotion allowed by trust policy'
      : `promotion blocked by trust policy (${request.trust.band}, ${request.trust.score.toFixed(2)})`,
  };
}

export function computeDelegatedAuthorityLevel(chain: DelegationLink[]): number {
  return deriveAuthorityLevel(chain);
}

export function calculateTrustView(
  confidence: number,
  authorityLevel: number,
  evidenceStrength: number,
  weights = { confidenceWeight: 0.4, authorityWeight: 0.3, evidenceWeight: 0.3 },
): RelationshipTrustView {
  const score = computeTrustScore({ confidence, authorityLevel, evidenceStrength }, weights);
  const band = trustBand(score);
  return {
    score,
    band,
    evidenceIds: [],
  };
}

export function buildRelationshipTrustPacket(input: {
  relationshipId: string;
  revision: number;
  subjectId?: string;
  objectId?: string;
  relationshipKind?: string;
  governanceLevel: GovernanceTrustLevel;
  authorityChain: string[];
  trust: RelationshipTrustView;
  ledgerEntryId?: string;
  receiptId?: string;
  capturedAt?: string;
}): RelationshipLedgerTrustPacket {
  return {
    relationshipId: input.relationshipId,
    revision: input.revision,
    subjectId: input.subjectId,
    objectId: input.objectId,
    relationshipKind: input.relationshipKind,
    governanceLevel: input.governanceLevel,
    authorityChain: [...input.authorityChain],
    trust: {
      score: input.trust.score,
      band: input.trust.band,
      evidenceIds: [...input.trust.evidenceIds],
      authority: input.trust.authority ? { ...input.trust.authority } : undefined,
      provenance: input.trust.provenance ? { ...input.trust.provenance } : undefined,
    },
    ledgerEntryId: input.ledgerEntryId,
    receiptId: input.receiptId,
    capturedAt: input.capturedAt,
  };
}

function canonicalizeJson(value: unknown): string {
  return JSON.stringify(sortValue(value));
}

function sortValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(sortValue);
  }
  if (!value || typeof value !== 'object') {
    return value;
  }
  const result: Record<string, unknown> = {};
  for (const key of Object.keys(value as Record<string, unknown>).sort()) {
    const entry = (value as Record<string, unknown>)[key];
    if (entry !== undefined) {
      result[key] = sortValue(entry);
    }
  }
  return result;
}

export function decayRelationshipTrust(
  trust: RelationshipTrustView,
  lastUpdated: string,
  now: string,
  halfLifeDays: number,
): RelationshipTrustView {
  const score = decayedTrustScore(trust.score, lastUpdated, now, halfLifeDays);
  return {
    ...trust,
    score,
    band: trustBand(score),
  };
}

export function inheritRelationshipTrust(
  parentTrust: RelationshipTrustView,
  attenuation: number,
): RelationshipTrustView {
  const score = inheritedTrustScore(parentTrust.score, attenuation);
  return {
    ...parentTrust,
    score,
    band: trustBand(score),
  };
}

export function resolveRelationshipTrust(
  left: RelationshipTrustView,
  right: RelationshipTrustView,
): RelationshipTrustView {
  return resolveTrustConflict(left, right);
}

export function shouldRetireTrustBearingModel(
  trustScore: number,
  lowTrustSince: string,
  now: string,
  policy: RetirementPolicy,
): boolean {
  return shouldRetireModel(trustScore, lowTrustSince, now, policy);
}
