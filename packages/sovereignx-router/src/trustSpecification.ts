import crypto from 'crypto';

import type { RelationshipLedgerTrustPacket, TrustBand } from './types.js';
import { trustBand } from './trust.js';

export type TrustDomain = 'ops' | 'safety' | 'finance' | 'compliance' | 'global';
export type TrustDecisionResult = 'allowed' | 'blocked' | 'warning';
export type TrustReplayMode = 'historical' | 'counterfactual';
export type TrustReplayScope = 'relationship' | 'domain' | 'global';

export interface TrustEvidenceRecord {
  evidenceId: string;
  artifactId?: string;
  relationshipId?: string;
  decisionId?: string;
  provenance: {
    originSystem: string;
    originActorId?: string;
    method: string;
    createdAt: string;
    standardsTraceabilityIds?: string[];
  };
  hash?: string;
  signature?: string;
}

export interface TrustAssertion {
  relationshipId: string;
  assertedById: string;
  assertedAt: string;
  score: number;
  band: TrustBand;
  evidenceIds: string[];
  authorityChain: string[];
  provenance: TrustEvidenceRecord['provenance'];
  rationale?: string;
}

export interface TrustEvaluationPolicy {
  policyId: string;
  policyVersion: string;
  domain: TrustDomain;
  governanceLevel: 'basic' | 'enhanced' | 'full';
  minTrustScore: number;
  requiredBand: TrustBand;
  preferHighTrustBand: boolean;
  minEvidenceCount: number;
  minAuthorityChainLength: number;
  confidenceWeight: number;
  authorityWeight: number;
  evidenceWeight: number;
  replayRequired: boolean;
  conformanceRequired: boolean;
  standardsTraceabilityIds?: string[];
}

export interface TrustEvaluationInput {
  relationshipId: string;
  subjectId?: string;
  objectId?: string;
  confidence: number;
  authorityLevel: number;
  evidenceStrength: number;
  evidenceIds: string[];
  authorityChain: string[];
  provenance: TrustEvidenceRecord['provenance'];
}

export interface TrustReceipt {
  receiptId: string;
  relationshipId: string;
  policyId: string;
  policyVersion: string;
  hash: string;
  signature: string;
  replayIndex: number;
  issuedAt: string;
}

export interface TrustEvaluationResult {
  relationshipId: string;
  policyId: string;
  policyVersion: string;
  domain: TrustDomain;
  score: number;
  band: TrustBand;
  result: TrustDecisionResult;
  reasons: string[];
  evidenceIds: string[];
  authorityChain: string[];
  policy: TrustEvaluationPolicy;
  assertion: TrustAssertion;
  receipt: TrustReceipt;
}

export interface TrustDecisionReport {
  decisionId: string;
  decisionType: 'routing' | 'promotion' | 'delegation' | 'governance';
  timestamp: string;
  relationshipId: string;
  artifactId: string;
  trustContext: {
    score: number;
    band: TrustBand;
    domain: TrustDomain;
    confidence: number;
    authority: number;
    evidenceStrength: number;
    evidenceIds: string[];
  };
  governanceContext: {
    tier: string;
    requiredScore: number;
    requiredBand: TrustBand;
    result: TrustDecisionResult;
    failedComponent: 'confidence' | 'authority' | 'evidence' | null;
  };
  routingContext: {
    candidates: Array<{
      id: string;
      baseScore: number;
      trustScore: number;
      governanceStatus: TrustDecisionResult;
      finalScore: number;
    }>;
    selectedCandidateId: string;
  };
  ledgerContext: {
    entryId: string;
    hash: string;
    previousHash: string | null;
    signature: string;
    replayIndex: number;
  };
  steps: Array<{
    name: string;
    description: string;
    data: Record<string, unknown>;
  }>;
  plainLanguageSummary: string;
}

export interface GovernanceFeedbackArtifact {
  feedbackId: string;
  createdAt: string;
  createdByStewardId: string;
  sourceDecisionId: string;
  sourceRelationshipId: string;
  sourceArtifactId: string;
  trigger: {
    type: 'governance_fail' | 'trust_band_change' | 'steward_flag' | 'anomaly';
    reason: string;
    severity: 'normal' | 'high' | 'critical';
  };
  trustSnapshot: {
    score: number;
    band: TrustBand;
    domain: TrustDomain;
    tier: string;
    result: TrustDecisionResult;
  };
  stewardAnalysis: {
    notes: Array<{
      id: string;
      authorStewardId: string;
      timestamp: string;
      text: string;
      tags: string[];
    }>;
    rootCause: string;
    impactedComponents: Array<'evidence' | 'authority' | 'algebra' | 'thresholds' | 'delegation' | 'routing'>;
  };
  proposedActions: Array<{
    id: string;
    type: 'adjust_thresholds' | 'adjust_algebra_weights' | 'request_evidence' | 'audit_delegation' | 'propose_amendment';
    description: string;
    payload: {
      before: Record<string, unknown>;
      after: Record<string, unknown>;
    };
  }>;
  governanceOutcome: {
    status: 'pending' | 'approved' | 'rejected';
    decidedAt: string | null;
    decidedByStewardId: string | null;
    decisionNotes: string | null;
  };
  links: {
    decisionReportId: string;
    governanceChangeProposalId: string | null;
    ledgerEntryId: string;
  };
}

export interface GovernanceConfigDiff {
  diffId: string;
  createdAt: string;
  currentConfigVersion: string;
  targetConfigVersion: string;
  domain: TrustDomain;
  tier: string;
  changes: Array<{
    path: string;
    before: unknown;
    after: unknown;
    rationale?: string;
  }>;
  replayReportIds: string[];
  trustReportIds: string[];
}

export interface TrustReplayReport {
  replayId: string;
  createdAt: string;
  mode: TrustReplayMode;
  scope: TrustReplayScope;
  configVersionUsed: string;
  timeRange: {
    start: string;
    end: string;
  };
  summary: {
    decisionsChanged: number;
    trustBandsChanged: number;
    governanceOutcomesChanged: number;
  };
  narrativeSummary: string;
  results: {
    decisions: Array<{
      decisionId: string;
      type: TrustDecisionReport['decisionType'];
      originalOutcome: TrustDecisionResult;
      replayedOutcome: TrustDecisionResult;
      changed: boolean;
      affectedComponents: string[];
    }>;
    trustDeltas: Array<{
      artifactId: string;
      originalScore: number;
      replayedScore: number;
      delta: number;
      bandChange: {
        from: TrustBand;
        to: TrustBand;
      } | null;
    }>;
    governanceDeltas: Array<{
      tier: string;
      originalStatus: TrustDecisionResult;
      replayedStatus: TrustDecisionResult;
      reason: string;
    }>;
  };
  hash: string;
  signature: string;
}

export interface TrustSpecificationConformance {
  replayable: boolean;
  deterministicUnderSameInputs: boolean;
  ledgerLinked: boolean;
  evidenceLinked: boolean;
  policyLinked: boolean;
  receiptLinked: boolean;
}

export interface TrustSpecificationBundle {
  policy: TrustEvaluationPolicy;
  input: TrustEvaluationInput;
  assertion: TrustAssertion;
  result: TrustEvaluationResult;
  receipt: TrustReceipt;
  ledgerPacket: RelationshipLedgerTrustPacket;
}

export function evaluateTrustPolicy(input: TrustEvaluationInput, policy: TrustEvaluationPolicy): TrustEvaluationResult {
  const score = clamp01(
    input.confidence * policy.confidenceWeight +
      input.authorityLevel * policy.authorityWeight +
      input.evidenceStrength * policy.evidenceWeight,
  );
  const band = trustBand(score);
  const trustAllowed = score >= policy.minTrustScore && trustBandRank(band) >= trustBandRank(policy.requiredBand);
  const result = trustAllowed ? 'allowed' : band === 'low' ? 'blocked' : 'warning';
  const reasons = [
    `trust.score=${score.toFixed(4)}`,
    `trust.band=${band}`,
    `policy.governanceLevel=${policy.governanceLevel}`,
  ];
  if (input.evidenceIds.length < policy.minEvidenceCount) {
    reasons.push(`evidence.count=${input.evidenceIds.length} below minimum ${policy.minEvidenceCount}`);
  }
  if (input.authorityChain.length < policy.minAuthorityChainLength) {
    reasons.push(`authority.chain.length=${input.authorityChain.length} below minimum ${policy.minAuthorityChainLength}`);
  }
  if (score < policy.minTrustScore) {
    reasons.push(`trust.score below minimum ${policy.minTrustScore}`);
  }
  if (trustBandRank(band) < trustBandRank(policy.requiredBand)) {
    reasons.push(`trust.band below required ${policy.requiredBand}`);
  }

  const assertion: TrustAssertion = {
    relationshipId: input.relationshipId,
    assertedById: input.provenance.originActorId ?? input.provenance.originSystem,
    assertedAt: input.provenance.createdAt,
    score,
    band,
    evidenceIds: [...input.evidenceIds],
    authorityChain: [...input.authorityChain],
    provenance: { ...input.provenance },
    rationale: result,
  };

  const receipt = createTrustReceipt({
    relationshipId: input.relationshipId,
    policyId: policy.policyId,
    policyVersion: policy.policyVersion,
    trustAssertion: assertion,
    replayIndex: 0,
  });

  return {
    relationshipId: input.relationshipId,
    policyId: policy.policyId,
    policyVersion: policy.policyVersion,
    domain: policy.domain,
    score,
    band,
    result,
    reasons,
    evidenceIds: [...input.evidenceIds],
    authorityChain: [...input.authorityChain],
    policy: { ...policy },
    assertion,
    receipt,
  };
}

export function createTrustReceipt(input: {
  relationshipId: string;
  policyId: string;
  policyVersion: string;
  trustAssertion: TrustAssertion;
  replayIndex: number;
  issuedAt?: string;
}): TrustReceipt {
  const issuedAt = input.issuedAt ?? input.trustAssertion.assertedAt;
  const hash = hashCanonicalJson({
    relationshipId: input.relationshipId,
    policyId: input.policyId,
    policyVersion: input.policyVersion,
    trustAssertion: input.trustAssertion,
    replayIndex: input.replayIndex,
    issuedAt,
  });
  return {
    receiptId: `trust-receipt-${hash.slice(0, 16)}`,
    relationshipId: input.relationshipId,
    policyId: input.policyId,
    policyVersion: input.policyVersion,
    hash,
    signature: hash,
    replayIndex: input.replayIndex,
    issuedAt,
  };
}

export function buildTrustDecisionReport(input: {
  decisionId: string;
  decisionType: TrustDecisionReport['decisionType'];
  artifactId: string;
  relationshipId: string;
  trustResult: TrustEvaluationResult;
  candidates: TrustDecisionReport['routingContext']['candidates'];
  ledgerEntryId: string;
  previousHash: string | null;
  signature: string;
  replayIndex: number;
  narrativeSummary: string;
}): TrustDecisionReport {
  const selectedCandidateId = pickBestCandidateId(input.candidates);
  return {
    decisionId: input.decisionId,
    decisionType: input.decisionType,
    timestamp: input.trustResult.receipt.issuedAt,
    relationshipId: input.relationshipId,
    artifactId: input.artifactId,
    trustContext: {
      score: input.trustResult.score,
      band: input.trustResult.band,
      domain: input.trustResult.domain,
      confidence: input.trustResult.assertion.score,
      authority: input.trustResult.assertion.authorityChain.length,
      evidenceStrength: Math.min(1, input.trustResult.assertion.evidenceIds.length / Math.max(1, input.trustResult.policy.minEvidenceCount || 1)),
      evidenceIds: [...input.trustResult.evidenceIds],
    },
    governanceContext: {
      tier: input.trustResult.policy.governanceLevel,
      requiredScore: input.trustResult.policy.minTrustScore,
      requiredBand: input.trustResult.policy.requiredBand,
      result: input.trustResult.result,
      failedComponent:
        input.trustResult.reasons.some((reason) => reason.includes('evidence.count')) ? 'evidence'
          : input.trustResult.reasons.some((reason) => reason.includes('authority.chain.length')) ? 'authority'
          : input.trustResult.reasons.some((reason) => reason.includes('trust.score')) ? 'confidence'
          : null,
    },
    routingContext: {
      candidates: [...input.candidates],
      selectedCandidateId,
    },
    ledgerContext: {
      entryId: input.ledgerEntryId,
      hash: input.signature,
      previousHash: input.previousHash,
      signature: input.signature,
      replayIndex: input.replayIndex,
    },
    steps: [
      {
        name: 'inputs_collected',
        description: 'Trust inputs were gathered from confidence, authority, and evidence.',
        data: {
          confidence: input.trustResult.assertion.score,
          authorityChain: [...input.trustResult.assertion.authorityChain],
          evidenceIds: [...input.trustResult.assertion.evidenceIds],
        },
      },
      {
        name: 'algebra_computed',
        description: `Trust score ${input.trustResult.score.toFixed(3)} (${input.trustResult.band} band) was computed from confidence, authority, and evidence using recorded weights.`,
        data: {
          score: input.trustResult.score,
          band: input.trustResult.band,
          policyId: input.trustResult.policy.policyId,
          policyVersion: input.trustResult.policy.policyVersion,
        },
      },
      {
        name: 'governance_evaluated',
        description: `Governance tier '${input.trustResult.policy.governanceLevel}' requires trust >= ${input.trustResult.policy.minTrustScore} and band '${input.trustResult.policy.requiredBand}'.`,
        data: {
          tier: input.trustResult.policy.governanceLevel,
          requiredScore: input.trustResult.policy.minTrustScore,
          requiredBand: input.trustResult.policy.requiredBand,
          result: input.trustResult.result,
        },
      },
      {
        name: 'routing_scored',
        description: 'The highest-scoring candidate was selected under the constitutional routing rules.',
        data: {
          selectedCandidateId,
        },
      },
      {
        name: 'final_decision',
        description: input.narrativeSummary,
        data: {},
      },
    ],
    plainLanguageSummary: input.narrativeSummary,
  };
}

function pickBestCandidateId(candidates: TrustDecisionReport['routingContext']['candidates']): string {
  if (candidates.length === 0) {
    return '';
  }
  let best = candidates[0];
  for (const candidate of candidates.slice(1)) {
    if (candidate.finalScore > best.finalScore) {
      best = candidate;
    }
  }
  return best.id;
}

export function buildGovernanceFeedbackArtifact(input: GovernanceFeedbackArtifact): GovernanceFeedbackArtifact {
  return clone(input);
}

export function buildGovernanceConfigDiff(input: GovernanceConfigDiff): GovernanceConfigDiff {
  return clone(input);
}

export function buildTrustReplayReport(input: TrustReplayReport): TrustReplayReport {
  return clone(input);
}

export function buildTrustLedgerTrustPacket(input: RelationshipLedgerTrustPacket): RelationshipLedgerTrustPacket {
  return clone(input);
}

export function buildTrustSpecificationBundle(input: TrustSpecificationBundle): TrustSpecificationBundle {
  return {
    policy: { ...input.policy },
    input: { ...input.input, evidenceIds: [...input.input.evidenceIds], authorityChain: [...input.input.authorityChain], provenance: { ...input.input.provenance } },
    assertion: { ...input.assertion, evidenceIds: [...input.assertion.evidenceIds], authorityChain: [...input.assertion.authorityChain], provenance: { ...input.assertion.provenance } },
    result: {
      ...input.result,
      reasons: [...input.result.reasons],
      evidenceIds: [...input.result.evidenceIds],
      authorityChain: [...input.result.authorityChain],
      policy: { ...input.result.policy },
      assertion: { ...input.result.assertion, evidenceIds: [...input.result.assertion.evidenceIds], authorityChain: [...input.result.assertion.authorityChain], provenance: { ...input.result.assertion.provenance } },
      receipt: { ...input.result.receipt },
    },
    receipt: { ...input.receipt },
    ledgerPacket: {
      ...input.ledgerPacket,
      authorityChain: [...input.ledgerPacket.authorityChain],
      trust: {
        ...input.ledgerPacket.trust,
        evidenceIds: [...input.ledgerPacket.trust.evidenceIds],
        authority: input.ledgerPacket.trust.authority ? { ...input.ledgerPacket.trust.authority } : undefined,
        provenance: input.ledgerPacket.trust.provenance ? { ...input.ledgerPacket.trust.provenance } : undefined,
      },
    },
  };
}

function hashCanonicalJson(value: unknown): string {
  return crypto.createHash('sha256').update(canonicalJson(value)).digest('hex');
}

function canonicalJson(value: unknown): string {
  return JSON.stringify(sortObject(value));
}

function sortObject(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(sortObject);
  }
  if (!value || typeof value !== 'object') {
    return value;
  }
  const result: Record<string, unknown> = {};
  for (const key of Object.keys(value as Record<string, unknown>).sort()) {
    const item = (value as Record<string, unknown>)[key];
    if (item !== undefined) {
      result[key] = sortObject(item);
    }
  }
  return result;
}

function clamp01(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.min(1, Math.max(0, value));
}

function trustBandRank(band: TrustBand): number {
  switch (band) {
    case 'low':
      return 0;
    case 'medium':
      return 1;
    case 'high':
      return 2;
  }
}

function clone<T>(value: T): T {
  return structuredClone(value);
}
