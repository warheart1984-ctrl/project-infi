import crypto from 'node:crypto';

import type { RelationshipLedgerTrustPacket, TrustBand, RouteEvaluation } from './types.js';
import type { GovernanceTrustPolicy } from './trust.js';
import type { TrustReplayMode, TrustReplayReport, TrustReplayScope } from './trustSpecification.js';

export type RouteDecisionStatus = 'allowed' | 'warning' | 'blocked';

export interface RouteGovernanceDecision {
  result: RouteDecisionStatus;
  governanceFactor: number;
  tier: string;
  reason: string;
  constraintsApplied: string[];
  decidedBy: string;
  decidedAt: string;
  configVersion?: string;
}

export interface RouteDecisionReplayContext {
  replayId?: string;
  mode?: TrustReplayMode;
  scope?: TrustReplayScope;
  report?: TrustReplayReport | null;
  validation?: unknown;
}

export interface RouteDecisionProvenance {
  originSystem: string;
  originActorId?: string;
  method: string;
  standardsTraceabilityIds?: string[];
}

export interface RouteDecisionArtifactSignature {
  algorithm: 'HMAC-SHA256';
  signer: string;
  signedAt: string;
  value: string;
}

export interface RouteTrustPolicy extends GovernanceTrustPolicy {
  requiredBand?: TrustBand;
  minEvidenceCount?: number;
  minAuthorityChainLength?: number;
}

export interface CanonicalRouteDecisionArtifact {
  version: '1.0';
  artifactId: string;
  requestId: string;
  orgId: string;
  customerId?: string;
  relationshipId: string;
  createdAt: string;
  trustPacket: RelationshipLedgerTrustPacket;
  routeEvaluation: RouteEvaluation;
  governance: RouteGovernanceDecision;
  replay?: RouteDecisionReplayContext;
  provenance: RouteDecisionProvenance;
  signature?: RouteDecisionArtifactSignature;
}

export interface BuildRouteDecisionArtifactInput {
  artifactId?: string;
  requestId: string;
  orgId: string;
  customerId?: string;
  relationshipId: string;
  trustPacket: RelationshipLedgerTrustPacket;
  trustPolicy: RouteTrustPolicy;
  routeEvaluation: RouteEvaluation;
  provenance: RouteDecisionProvenance;
  decidedBy?: string;
  decidedAt?: string;
  configVersion?: string;
  replay?: RouteDecisionReplayContext;
  signingSecret?: string;
  signer?: string;
}

export function evaluateRouteGovernance(
  trustPacket: RelationshipLedgerTrustPacket,
  trustPolicy: RouteTrustPolicy,
  input: {
    decidedBy?: string;
    decidedAt?: string;
    configVersion?: string;
  } = {},
): RouteGovernanceDecision {
  const decidedAt = input.decidedAt ?? new Date().toISOString();
  const decidedBy = input.decidedBy ?? 'governance-kernel';
  const requiredBand = trustPolicy.requiredBand ?? trustPolicy.minTrustBand ?? trustPacket.trust.band;
  const minEvidenceCount = trustPolicy.minEvidenceCount ?? defaultMinimumEvidenceCount(trustPacket.governanceLevel);
  const minAuthorityChainLength = trustPolicy.minAuthorityChainLength ?? defaultMinimumAuthorityChainLength(trustPacket.governanceLevel);
  const constraintsApplied: string[] = [
    `requires_trustScore>=${trustPolicy.minTrustScore}`,
    `requires_trustBand>=${requiredBand}`,
    `requires_evidence_count>=${minEvidenceCount}`,
    `requires_authority_chain_length>=${minAuthorityChainLength}`,
    'requires_trust_signature',
  ];

  const missingSignature = !trustPacket.signature?.value;
  const scoreMeets = trustPacket.trust.score >= trustPolicy.minTrustScore;
  const bandMeets = compareBand(trustPacket.trust.band, requiredBand) >= 0;
  const evidenceMeets = trustPacket.trust.evidenceIds.length >= minEvidenceCount;
  const authorityMeets = trustPacket.authorityChain.length >= minAuthorityChainLength;
  const trustBandGap = compareBand(trustPacket.trust.band, requiredBand);
  const trustScoreGap = trustPacket.trust.score - trustPolicy.minTrustScore;

  if (missingSignature) {
    return {
      result: 'blocked',
      governanceFactor: 0,
      tier: trustPolicy.governanceLevel,
      reason: 'signed trust packet is required',
      constraintsApplied,
      decidedBy,
      decidedAt,
      configVersion: input.configVersion,
    };
  }

  if (!evidenceMeets || !authorityMeets) {
    return {
      result: 'blocked',
      governanceFactor: 0,
      tier: trustPolicy.governanceLevel,
      reason: !evidenceMeets
        ? 'insufficient evidence for routing'
        : 'authority chain does not satisfy governance policy',
      constraintsApplied,
      decidedBy,
      decidedAt,
      configVersion: input.configVersion,
    };
  }

  if (scoreMeets && bandMeets) {
    return {
      result: 'allowed',
      governanceFactor: 1,
      tier: trustPolicy.governanceLevel,
      reason: 'trust packet satisfies governance policy',
      constraintsApplied,
      decidedBy,
      decidedAt,
      configVersion: input.configVersion,
    };
  }

  const warningEligible = trustScoreGap >= -0.05 && trustBandGap >= -1;
  if (warningEligible) {
    return {
      result: 'warning',
      governanceFactor: 0.7,
      tier: trustPolicy.governanceLevel,
      reason: scoreMeets
        ? 'trust band is one step below the governance requirement'
        : 'trust score is near the governance threshold',
      constraintsApplied,
      decidedBy,
      decidedAt,
      configVersion: input.configVersion,
    };
  }

  return {
    result: 'blocked',
    governanceFactor: 0,
    tier: trustPolicy.governanceLevel,
      reason: scoreMeets
      ? 'trust band does not satisfy governance policy'
      : 'trust score does not satisfy governance policy',
    constraintsApplied,
    decidedBy,
    decidedAt,
    configVersion: input.configVersion,
  };
}

function defaultMinimumEvidenceCount(governanceLevel: string): number {
  return governanceLevel === 'full' ? 3 : governanceLevel === 'enhanced' ? 2 : 1;
}

function defaultMinimumAuthorityChainLength(governanceLevel: string): number {
  return governanceLevel === 'full' ? 3 : governanceLevel === 'enhanced' ? 2 : 1;
}

export function buildRouteDecisionArtifact(input: BuildRouteDecisionArtifactInput): CanonicalRouteDecisionArtifact {
  if (!input.trustPacket.signature?.value) {
    throw new Error('signed trust packet is required');
  }

  const createdAt = input.decidedAt ?? new Date().toISOString();
  const governance = evaluateRouteGovernance(input.trustPacket, input.trustPolicy, {
    decidedBy: input.decidedBy,
    decidedAt: createdAt,
    configVersion: input.configVersion,
  });
  const unsignedArtifact: CanonicalRouteDecisionArtifact = {
    version: '1.0',
    artifactId: input.artifactId ?? input.requestId,
    requestId: input.requestId,
    orgId: input.orgId,
    customerId: input.customerId,
    relationshipId: input.relationshipId,
    createdAt,
    trustPacket: input.trustPacket,
    routeEvaluation: cloneRouteEvaluation(input.routeEvaluation),
    governance,
    replay: input.replay ? cloneRouteReplayContext(input.replay) : undefined,
    provenance: {
      ...input.provenance,
      standardsTraceabilityIds: input.provenance.standardsTraceabilityIds ? [...input.provenance.standardsTraceabilityIds] : undefined,
    },
  };

  const signingSecret = input.signingSecret?.trim() || 'sovereignx-router-route-decision';
  const signer = input.signer ?? 'sovereignx-router';
  const signatureValue = crypto.createHmac('sha256', signingSecret).update(canonicalizeJson(unsignedArtifact)).digest('hex');

  return {
    ...unsignedArtifact,
    signature: {
      algorithm: 'HMAC-SHA256',
      signer,
      signedAt: createdAt,
      value: signatureValue,
    },
  };
}

export function verifyRouteDecisionArtifact(
  artifact: CanonicalRouteDecisionArtifact,
  signingSecret: string,
): boolean {
  if (!artifact.signature || artifact.signature.algorithm !== 'HMAC-SHA256') {
    return false;
  }

  const { signature, ...unsignedArtifact } = artifact;
  const expected = crypto.createHmac('sha256', signingSecret).update(canonicalizeJson(unsignedArtifact)).digest('hex');
  return expected === signature.value;
}

function compareBand(left: TrustBand, right: TrustBand): number {
  return bandRank(left) - bandRank(right);
}

function bandRank(band: TrustBand): number {
  switch (band) {
    case 'low':
      return 0;
    case 'medium':
      return 1;
    case 'high':
      return 2;
  }
  return 0;
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

function cloneRouteEvaluation(routeEvaluation: RouteEvaluation): RouteEvaluation {
  return structuredClone(routeEvaluation);
}

function cloneRouteReplayContext(replay: RouteDecisionReplayContext): RouteDecisionReplayContext {
  return structuredClone(replay);
}
