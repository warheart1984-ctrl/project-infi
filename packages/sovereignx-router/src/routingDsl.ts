import type { RelationshipTrustView, TrustBand } from './types.js';

export type DirectiveKind = 'require' | 'prefer' | 'avoid' | 'enforce';
export type Operator = '=' | '!=' | '<' | '<=' | '>' | '>=';

export const TRUST_PATHS = ['trust.score', 'trust.band'] as const;

export interface RoutingDslClause {
  kind: DirectiveKind;
  path: string;
  op: Operator;
  value: string;
  annotations: Record<string, string>;
}

export interface ParsedRoutingDsl {
  clauses: RoutingDslClause[];
}

export interface CompiledRoutingConstraint extends RoutingDslClause {
  validatedPath: string;
}

export interface CompiledRoutingPolicy {
  clauses: CompiledRoutingConstraint[];
}

export interface TrustPromotionRequest {
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

export interface DelegationLink {
  fromId: string;
  toId: string;
  trustScore: number;
  trustBand: TrustBand;
  evidenceIds: string[];
}

export interface TrustAuditPacket {
  relationshipId: string;
  revision: number;
  trustScore: number;
  trustBand: TrustBand;
  evidenceIds: string[];
  authorityChain: string[];
  provenance: {
    originSystem: string;
    originActorId?: string;
    method: string;
    standardsTraceabilityIds?: string[];
  };
  receipt: {
    receiptId: string;
    relationshipId: string;
    revision: number;
    ledgerEntryId: string;
    timestamp: string;
    hash: string;
    signature: {
      algorithm: 'Ed25519';
      value: string;
    };
    replayIndex: number;
  };
}

export interface CandidateModel {
  id: string;
  name: string;
  governanceScore: number;
  costScore: number;
  performanceScore: number;
  trustScore: number;
  trustBand: TrustBand;
  relationshipTrust?: RelationshipTrustView;
}

export interface TrustHeuristics {
  minTrustScore: number;
  preferHighTrustBand: boolean;
  minTrustBand?: TrustBand;
}

export interface RetirementPolicy {
  minTrustScore: number;
  maxLowTrustDays: number;
}

export const TRUST_GOVERNANCE_TIERS = {
  basic: {
    minTrustBand: 'low' as TrustBand,
    minTrustScore: 0.0,
  },
  standard: {
    minTrustBand: 'medium' as TrustBand,
    minTrustScore: 0.4,
  },
  regulated: {
    minTrustBand: 'high' as TrustBand,
    minTrustScore: 0.7,
  },
} as const;

export function validateRoutingPath(path: string): boolean {
  if (TRUST_PATHS.includes(path as (typeof TRUST_PATHS)[number])) {
    return true;
  }
  if (path.startsWith('governance.') || path.startsWith('cost.') || path.startsWith('performance.') || path.startsWith('drift.') || path.startsWith('lineage.') || path.startsWith('conformance.')) {
    return true;
  }
  throw new Error(`Unknown DSL path: ${path}`);
}

export function validatePath(path: string): boolean {
  return validateRoutingPath(path);
}

export function parseRoutingDsl(dsl: string): ParsedRoutingDsl {
  const clauses: RoutingDslClause[] = [];
  for (const rawLine of dsl.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;

    const match = line.match(/^(require|prefer|avoid|enforce)\s+([a-zA-Z0-9_.]+)\s*(=|!=|<=|>=|<|>)\s*([^[]+?)(?:\s*\[(.+)\])?$/);
    if (!match) {
      throw new Error(`Invalid routing DSL clause: ${line}`);
    }

    const [, kind, path, op, value, annotations] = match;
    validateRoutingPath(path);
    clauses.push({
      kind: kind as DirectiveKind,
      path,
      op: op as Operator,
      value: value.trim(),
      annotations: parseAnnotations(annotations),
    });
  }
  return { clauses };
}

export function compileRoutingDsl(policy: string | ParsedRoutingDsl): CompiledRoutingPolicy {
  const parsed = typeof policy === 'string' ? parseRoutingDsl(policy) : policy;
  return {
    clauses: parsed.clauses.map((clause) => ({
      ...clause,
      validatedPath: clause.path,
    })),
  };
}

export function compileToGraphConstraints(policy: string | ParsedRoutingDsl): CompiledRoutingConstraint[] {
  return compileRoutingDsl(policy).clauses;
}

export function computeTrustScore(
  inputs: { confidence: number; authorityLevel: number; evidenceStrength: number },
  weights: { confidenceWeight: number; authorityWeight: number; evidenceWeight: number },
): number {
  const score =
    inputs.confidence * weights.confidenceWeight +
    inputs.authorityLevel * weights.authorityWeight +
    inputs.evidenceStrength * weights.evidenceWeight;
  return clamp01(score);
}

export function trustBand(score: number): TrustBand {
  if (score < 0.33) return 'low';
  if (score < 0.66) return 'medium';
  return 'high';
}

export function canPromote(trustScore: number, trustBandValue: TrustBand, heuristics: TrustHeuristics): boolean {
  if (trustScore < heuristics.minTrustScore) return false;
  if (heuristics.minTrustBand) {
    if (trustBandRank(trustBandValue) < trustBandRank(heuristics.minTrustBand)) return false;
  } else if (trustBandValue === 'low') {
    return false;
  }
  if (heuristics.preferHighTrustBand && trustBandValue !== 'high') return false;
  return true;
}

export function decayedTrustScore(baseScore: number, lastUpdated: string, now: string, halfLifeDays: number): number {
  const elapsedMs = Date.parse(now) - Date.parse(lastUpdated);
  if (!Number.isFinite(elapsedMs) || halfLifeDays <= 0) return clamp01(baseScore);
  const days = elapsedMs / (1000 * 60 * 60 * 24);
  const decayFactor = Math.pow(0.5, days / halfLifeDays);
  return clamp01(baseScore * decayFactor);
}

export function inheritedTrustScore(parentScore: number, attenuation: number): number {
  return clamp01(parentScore * attenuation);
}

export function resolveTrustConflict(
  a: RelationshipTrustView,
  b: RelationshipTrustView,
): RelationshipTrustView {
  const aPower = a.score * Math.max(1, a.evidenceIds.length);
  const bPower = b.score * Math.max(1, b.evidenceIds.length);
  return aPower >= bPower ? a : b;
}

export function shouldRetireModel(trustScore: number, lowTrustSince: string, now: string, policy: RetirementPolicy): boolean {
  if (trustScore >= policy.minTrustScore) return false;
  const elapsedMs = Date.parse(now) - Date.parse(lowTrustSince);
  if (!Number.isFinite(elapsedMs)) return false;
  const days = elapsedMs / (1000 * 60 * 60 * 24);
  return days >= policy.maxLowTrustDays;
}

export function deriveAuthorityLevel(chain: DelegationLink[]): number {
  if (chain.length === 0) return 0;
  return clamp01(chain.reduce((acc, link) => acc * clamp01(link.trustScore), 1));
}

export function applyTrustToCandidateModel(
  model: CandidateModel,
  trust: RelationshipTrustView | undefined,
): CandidateModel {
  if (!trust) {
    return {
      ...model,
      trustScore: model.trustScore,
      trustBand: model.trustBand,
    };
  }

  return {
    ...model,
    trustScore: clamp01(trust.score),
    trustBand: trust.band,
    relationshipTrust: {
      score: clamp01(trust.score),
      band: trust.band,
      evidenceIds: [...trust.evidenceIds],
      authority: trust.authority ? { ...trust.authority } : undefined,
      provenance: trust.provenance ? { ...trust.provenance } : undefined,
    },
  };
}

export function buildTrustAuditPacket(input: {
  relationshipId: string;
  revision: number;
  trust: RelationshipTrustView;
  authorityChain: string[];
  provenance: {
    originSystem: string;
    originActorId?: string;
    method: string;
    standardsTraceabilityIds?: string[];
  };
  receipt: TrustAuditPacket['receipt'];
}): TrustAuditPacket {
  return {
    relationshipId: input.relationshipId,
    revision: input.revision,
    trustScore: clamp01(input.trust.score),
    trustBand: input.trust.band,
    evidenceIds: [...input.trust.evidenceIds],
    authorityChain: [...input.authorityChain],
    provenance: {
      originSystem: input.provenance.originSystem,
      originActorId: input.provenance.originActorId,
      method: input.provenance.method,
      standardsTraceabilityIds: input.provenance.standardsTraceabilityIds ? [...input.provenance.standardsTraceabilityIds] : undefined,
    },
    receipt: {
      ...input.receipt,
      signature: {
        algorithm: 'Ed25519',
        value: input.receipt.signature.value,
      },
    },
  };
}

function parseAnnotations(value: string | undefined): Record<string, string> {
  if (!value) return {};
  return value
    .split(/\s+/)
    .map((entry) => entry.trim())
    .filter(Boolean)
    .reduce<Record<string, string>>((annotations, entry) => {
      const [key, rawValue] = entry.split('=');
      if (key && rawValue !== undefined) {
        annotations[key] = rawValue;
      }
      return annotations;
    }, {});
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
