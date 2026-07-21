import crypto from 'crypto';

import type { TrustBand } from './trust.js';
import type {
  GovernanceConfigDiff,
  TrustDecisionResult,
  TrustDomain,
  TrustReplayMode,
  TrustReplayReport,
  TrustReplayScope,
} from './trustSpecification.js';

export type ConstitutionalArtifactKind =
  | 'invariant'
  | 'clause'
  | 'config'
  | 'delegation-law'
  | 'trust-algebra'
  | 'conformance-rule'
  | 'amendment';

export type ConstitutionalPlane = 'governance' | 'knowledge' | 'execution' | 'control';
export type ContinuityDecision = 'approved' | 'rejected' | 'changes_requested';
export type PlaneConformanceStatus = 'conformant' | 'partial' | 'non-conformant';
export type ContinuitySeverity = 'normal' | 'warning' | 'critical';
export type PolityLifecycleStage = 'birth' | 'growth' | 'governance' | 'replay' | 'renewal';
export type GovernanceKernelTier = 'policy' | 'trust-aware' | 'clause-reasoning' | 'cross-plane' | 'replay-integrated';

export interface ConstitutionalArtifactRevision {
  artifactId: string;
  artifactKind: ConstitutionalArtifactKind;
  version: string;
  parentId: string | null;
  previousHash: string | null;
  hash: string;
  signature: string;
  timestamp: string;
  replayContext: {
    mode: TrustReplayMode;
    scope: TrustReplayScope;
    configVersionUsed: string;
    timeRange: {
      start: string;
      end: string;
    };
  };
  content: Record<string, unknown>;
}

export interface ContinuityValidationResult {
  valid: boolean;
  reasons: string[];
  chain: Array<{
    artifactId: string;
    parentId: string | null;
    hash: string;
    timestamp: string;
  }>;
}

export interface GovernanceChangeProposal {
  proposalId: string;
  createdAt: string;
  createdByStewardId: string;
  motivation: {
    summary: string;
    linkedDecisionIds: string[];
    linkedFeedbackIds: string[];
    linkedReplayReportIds: string[];
    externalPolicyReferences: string[];
  };
  currentConfigVersion: string;
  targetConfigVersion: string;
  affectedDomains: TrustDomain[];
  affectedTiers: string[];
  affectedDelegationChains: string[];
  affectedTrustAlgebraComponents: string[];
  affectedConformanceRules: string[];
  proposedChanges: Array<{
    path: string;
    operation: 'add' | 'modify' | 'retire';
    before: unknown;
    after: unknown;
    retirementMarker?: string;
  }>;
  riskAssessment: {
    impactLevel: 'low' | 'medium' | 'high' | 'critical';
    notes: string;
  };
}

export interface ReplayValidationContract {
  configVersionUsed: string;
  scope: TrustReplayScope;
  requiredDomains: TrustDomain[];
  requiredRelationships: string[];
  requiredTiers: string[];
  requiredRoutingDecisions: string[];
  requiredTrustArtifacts: string[];
  requireHistoricalReplay: boolean;
  requireCounterfactualReplay: boolean;
  maxAllowedDecisionsChanged?: number;
  maxAllowedTrustBandDrops?: number;
  maxAllowedGovernanceRegressions?: number;
}

export interface ReplayValidationResult {
  passed: boolean;
  reasons: string[];
  metrics: {
    decisionsChanged: number;
    trustDeltas: number;
    governanceDeltas: number;
    routingChanges: number;
    promotionChanges: number;
    anomalyResolution: number;
  };
  report: TrustReplayReport;
}

export interface PlaneConformanceRule {
  id: string;
  description: string;
  required: boolean;
}

export interface PlaneConformanceCheck {
  plane: ConstitutionalPlane;
  status: PlaneConformanceStatus;
  reasons: string[];
  evidenceIds: string[];
  replayable: boolean;
  lineagePreserved: boolean;
  trustAligned: boolean;
}

export interface ConstitutionalConformanceReport {
  reportId: string;
  createdAt: string;
  checks: PlaneConformanceCheck[];
  signedReceipt: ContinuityReceipt;
}

export interface ConstitutionalInteroperabilityContract {
  sharedIdentityRequired: boolean;
  sharedTrustModelRequired: boolean;
  sharedEvidenceModelRequired: boolean;
  replayUnifiedRequired: boolean;
  conformanceUnifiedRequired: boolean;
}

export interface ConstitutionalDiagnosisReport {
  diagnosisId: string;
  createdAt: string;
  trustDeltas: string[];
  governanceDeltas: string[];
  routingDeltas: string[];
  delegationFailures: string[];
  invariantViolations: string[];
  replayRegressions: string[];
  conformanceFailures: string[];
  recommendedAmendments: string[];
}

export interface PolityLifecycleEvent {
  eventId: string;
  stage: PolityLifecycleStage;
  artifactId: string;
  createdAt: string;
  summary: string;
  outcome?: string;
}

export interface ContinuityReceipt {
  receiptId: string;
  subjectId: string;
  subjectKind: ConstitutionalArtifactKind | 'polity' | 'plane' | 'diagnosis';
  parentId: string | null;
  hash: string;
  signature: string;
  replayIndex: number;
  issuedAt: string;
}

export interface CSAAuthorityContract {
  role: 'Constitutional Steward-Architect';
  authorities: {
    constitutionalInvariants: { define: boolean; amend: boolean; retire: boolean };
    governanceDoctrine: { createClauses: boolean; modifyClauses: boolean; retireClauses: boolean };
    governanceConfig: { proposeChanges: boolean; approveChanges: boolean; rejectChanges: boolean };
    trustAlgebra: { define: boolean; amend: boolean };
    delegationLaw: { define: boolean; amend: boolean };
    conformanceRules: { define: boolean; amend: boolean };
    constitutionalEvents: { issue: boolean; review: boolean };
    controlPlaneSpec: { define: boolean; amend: boolean };
  };
  constraints: {
    evidenceRequired: boolean;
    ledgerRecordingRequired: boolean;
    replayValidationRequired: boolean;
  };
}

export interface GovernanceKernelV3Input {
  actionType: 'routing' | 'promotion' | 'delegation' | 'deployment' | 'audit';
  domain: TrustDomain;
  tier: string;
  trustScore: number;
  trustBand: TrustBand;
  evidenceIds: string[];
  authorityChain: string[];
  policyResult: TrustDecisionResult;
  policyFactor: number;
  clauseViolations: string[];
  conformance: ConstitutionalConformanceReport;
  replay?: ReplayValidationResult;
}

export interface GovernanceKernelV3Decision {
  result: 'allowed' | 'blocked' | 'warning';
  governanceFactor: number;
  tier: string;
  reasons: string[];
  clauseViolations: string[];
  replayRequired: boolean;
  conformanceStatus: PlaneConformanceStatus;
}

export function createContinuityReceipt(input: {
  subjectId: string;
  subjectKind: ContinuityReceipt['subjectKind'];
  parentId: string | null;
  payload: unknown;
  replayIndex: number;
  issuedAt: string;
}): ContinuityReceipt {
  const hash = hashCanonical(input.payload);
  return {
    receiptId: `continuity-${hash.slice(0, 16)}`,
    subjectId: input.subjectId,
    subjectKind: input.subjectKind,
    parentId: input.parentId,
    hash,
    signature: hash,
    replayIndex: input.replayIndex,
    issuedAt: input.issuedAt,
  };
}

export function validateConstitutionalLineage(revisions: ConstitutionalArtifactRevision[]): ContinuityValidationResult {
  const ordered = [...revisions].sort((left, right) => {
    const leftTime = Date.parse(left.timestamp);
    const rightTime = Date.parse(right.timestamp);
    if (leftTime !== rightTime) {
      return leftTime - rightTime;
    }
    return left.artifactId.localeCompare(right.artifactId);
  });

  const reasons: string[] = [];
  const seen = new Set<string>();

  ordered.forEach((revision, index) => {
    if (seen.has(revision.artifactId)) {
      reasons.push(`duplicate artifactId ${revision.artifactId}`);
    }
    seen.add(revision.artifactId);

    if (!revision.artifactId) {
      reasons.push('missing artifactId');
    }
    if (!revision.hash) {
      reasons.push(`missing hash for ${revision.artifactId}`);
    }
    if (!revision.signature) {
      reasons.push(`missing signature for ${revision.artifactId}`);
    }
    if (!revision.timestamp) {
      reasons.push(`missing timestamp for ${revision.artifactId}`);
    }

    if (index === 0) {
      if (revision.parentId !== null) {
        reasons.push(`root artifact ${revision.artifactId} must not declare a parentId`);
      }
      if (revision.previousHash !== null) {
        reasons.push(`root artifact ${revision.artifactId} must not declare previousHash`);
      }
      return;
    }

    const previous = ordered[index - 1];
    if (revision.parentId !== previous.artifactId) {
      reasons.push(
        `artifact ${revision.artifactId} parentId ${revision.parentId ?? 'null'} must point to previous artifact ${previous.artifactId}`,
      );
    }
    if (revision.previousHash !== previous.hash) {
      reasons.push(
        `artifact ${revision.artifactId} previousHash ${revision.previousHash ?? 'null'} does not match ${previous.artifactId}`,
      );
    }
  });

  return {
    valid: reasons.length === 0,
    reasons,
    chain: ordered.map((revision) => ({
      artifactId: revision.artifactId,
      parentId: revision.parentId,
      hash: revision.hash,
      timestamp: revision.timestamp,
    })),
  };
}

export function synthesizeGovernanceConfigDiff(input: {
  diffId: string;
  createdAt: string;
  currentConfigVersion: string;
  targetConfigVersion: string;
  domain: TrustDomain;
  tier: string;
  currentConfig: unknown;
  proposedConfig: unknown;
  replayReportIds?: string[];
  trustReportIds?: string[];
}): GovernanceConfigDiff {
  return {
    diffId: input.diffId,
    createdAt: input.createdAt,
    currentConfigVersion: input.currentConfigVersion,
    targetConfigVersion: input.targetConfigVersion,
    domain: input.domain,
    tier: input.tier,
    changes: diffObjects(input.currentConfig, input.proposedConfig),
    replayReportIds: input.replayReportIds ? [...input.replayReportIds] : [],
    trustReportIds: input.trustReportIds ? [...input.trustReportIds] : [],
  };
}

export function evaluateReplayValidation(contract: ReplayValidationContract, report: TrustReplayReport): ReplayValidationResult {
  const reasons: string[] = [];
  const decisionsChanged = report.summary.decisionsChanged;
  const trustDeltas = report.summary.trustBandsChanged;
  const governanceDeltas = report.summary.governanceOutcomesChanged;
  const routingChanges = report.results.decisions.filter((decision) => decision.changed && decision.type === 'routing').length;
  const promotionChanges = report.results.decisions.filter((decision) => decision.changed && decision.type === 'promotion').length;
  const anomalyResolution = report.results.governanceDeltas.filter((delta) => delta.replayedStatus !== 'blocked').length;

  if (contract.requireHistoricalReplay && report.mode !== 'historical' && report.mode !== 'counterfactual') {
    reasons.push('historical replay required');
  }
  if (contract.requireCounterfactualReplay && report.mode !== 'counterfactual') {
    reasons.push('counterfactual replay required');
  }
  if (contract.scope !== report.scope && contract.scope !== 'global') {
    reasons.push(`replay scope ${report.scope} does not satisfy required scope ${contract.scope}`);
  }
  if (typeof contract.maxAllowedDecisionsChanged === 'number' && decisionsChanged > contract.maxAllowedDecisionsChanged) {
    reasons.push(`decisionsChanged ${decisionsChanged} exceeds ${contract.maxAllowedDecisionsChanged}`);
  }
  if (typeof contract.maxAllowedTrustBandDrops === 'number' && trustDeltas > contract.maxAllowedTrustBandDrops) {
    reasons.push(`trust band changes ${trustDeltas} exceeds ${contract.maxAllowedTrustBandDrops}`);
  }
  if (typeof contract.maxAllowedGovernanceRegressions === 'number' && governanceDeltas > contract.maxAllowedGovernanceRegressions) {
    reasons.push(`governance regressions ${governanceDeltas} exceeds ${contract.maxAllowedGovernanceRegressions}`);
  }

  const passed = reasons.length === 0;
  return {
    passed,
    reasons,
    metrics: {
      decisionsChanged,
      trustDeltas,
      governanceDeltas,
      routingChanges,
      promotionChanges,
      anomalyResolution,
    },
    report,
  };
}

export function evaluatePlaneConformance(
  checks: PlaneConformanceCheck[],
  rules: PlaneConformanceRule[],
): ConstitutionalConformanceReport {
  const augmentedChecks = checks.map((check) => {
    const reasons = [...check.reasons];
    for (const rule of rules) {
      if (rule.required && !check.replayable && rule.id.startsWith('replay')) {
        reasons.push(rule.description);
      }
    }
    const requiredRulesViolated = checksViolations(check, rules);
    return {
      ...check,
      status: requiredRulesViolated.length > 0 && check.status === 'conformant' ? 'partial' : check.status,
      reasons: [...reasons, ...requiredRulesViolated],
    };
  });

  const reportId = `conformance-${hashCanonical({ augmentedChecks, rules }).slice(0, 16)}`;
  const signedReceipt = createContinuityReceipt({
    subjectId: reportId,
    subjectKind: 'plane',
    parentId: null,
    payload: { augmentedChecks, rules },
    replayIndex: 0,
    issuedAt: new Date().toISOString(),
  });

  return {
    reportId,
    createdAt: signedReceipt.issuedAt,
    checks: augmentedChecks,
    signedReceipt,
  };
}

export function diagnoseConstitutionalDrift(input: {
  diagnosisId: string;
  createdAt: string;
  trustDeltas: string[];
  governanceDeltas: string[];
  routingDeltas: string[];
  delegationFailures: string[];
  invariantViolations: string[];
  replayRegressions: string[];
  conformanceFailures: string[];
}): ConstitutionalDiagnosisReport {
  return {
    diagnosisId: input.diagnosisId,
    createdAt: input.createdAt,
    trustDeltas: [...input.trustDeltas],
    governanceDeltas: [...input.governanceDeltas],
    routingDeltas: [...input.routingDeltas],
    delegationFailures: [...input.delegationFailures],
    invariantViolations: [...input.invariantViolations],
    replayRegressions: [...input.replayRegressions],
    conformanceFailures: [...input.conformanceFailures],
    recommendedAmendments: buildRecommendedAmendments(input),
  };
}

export function evaluateGovernanceKernelV3(input: GovernanceKernelV3Input): GovernanceKernelV3Decision {
  const reasons: string[] = [];
  const replayRequired = input.actionType === 'routing' || input.actionType === 'promotion' || input.actionType === 'deployment';
  const conformanceStatus = aggregatePlaneStatus(input.conformance.checks);
  let governanceFactor = clamp01(input.policyFactor);

  if (input.policyResult === 'blocked') {
    reasons.push('policy evaluation blocked the action');
    governanceFactor = 0;
  } else if (input.policyResult === 'warning') {
    reasons.push('policy evaluation issued a warning');
    governanceFactor = Math.min(governanceFactor, 0.7);
  }

  if (input.trustScore < 0.7) {
    reasons.push(`trust score ${input.trustScore.toFixed(3)} below advisory floor`);
    governanceFactor = Math.min(governanceFactor, 0.7);
  }
  if (input.trustBand === 'low') {
    reasons.push('low trust band constrains constitutional authority');
    governanceFactor = Math.min(governanceFactor, 0.5);
  }
  if (input.evidenceIds.length === 0) {
    reasons.push('no constitutional evidence supplied');
    governanceFactor = 0;
  }
  if (input.authorityChain.length === 0) {
    reasons.push('no traceable delegation chain supplied');
    governanceFactor = 0;
  }
  if (input.clauseViolations.length > 0) {
    reasons.push(...input.clauseViolations.map((violation) => `clause violation: ${violation}`));
    governanceFactor = 0;
  }
  if (conformanceStatus === 'non-conformant') {
    reasons.push('cross-plane conformance failed');
    governanceFactor = 0;
  }
  if (input.replay && !input.replay.passed) {
    reasons.push(...input.replay.reasons);
    governanceFactor = 0;
  }

  const result = governanceFactor === 0
    ? 'blocked'
    : governanceFactor < 1 || input.policyResult === 'warning'
      ? 'warning'
      : 'allowed';

  return {
    result,
    governanceFactor,
    tier: input.tier,
    reasons,
    clauseViolations: [...input.clauseViolations],
    replayRequired,
    conformanceStatus,
  };
}

export function buildPolityLifecycleEvent(input: {
  eventId: string;
  stage: PolityLifecycleStage;
  artifactId: string;
  createdAt: string;
  summary: string;
  outcome?: string;
}): PolityLifecycleEvent {
  return {
    eventId: input.eventId,
    stage: input.stage,
    artifactId: input.artifactId,
    createdAt: input.createdAt,
    summary: input.summary,
    outcome: input.outcome,
  };
}

export function buildCSAAuthorityContract(): CSAAuthorityContract {
  return {
    role: 'Constitutional Steward-Architect',
    authorities: {
      constitutionalInvariants: { define: true, amend: true, retire: true },
      governanceDoctrine: { createClauses: true, modifyClauses: true, retireClauses: true },
      governanceConfig: { proposeChanges: true, approveChanges: true, rejectChanges: true },
      trustAlgebra: { define: true, amend: true },
      delegationLaw: { define: true, amend: true },
      conformanceRules: { define: true, amend: true },
      constitutionalEvents: { issue: true, review: true },
      controlPlaneSpec: { define: true, amend: true },
    },
    constraints: {
      evidenceRequired: true,
      ledgerRecordingRequired: true,
      replayValidationRequired: true,
    },
  };
}

function checksViolations(
  check: PlaneConformanceCheck,
  rules: PlaneConformanceRule[],
): string[] {
  const violations: string[] = [];
  for (const rule of rules) {
    if (!rule.required) {
      continue;
    }
    if (!check.replayable && rule.id.includes('replay')) {
      violations.push(rule.description);
    }
    if (!check.lineagePreserved && rule.id.includes('lineage')) {
      violations.push(rule.description);
    }
    if (!check.trustAligned && rule.id.includes('trust')) {
      violations.push(rule.description);
    }
    if (check.status !== 'conformant' && rule.id.includes(check.plane)) {
      violations.push(rule.description);
    }
  }
  return violations;
}

function aggregatePlaneStatus(checks: PlaneConformanceCheck[]): PlaneConformanceStatus {
  if (checks.some((check) => check.status === 'non-conformant')) {
    return 'non-conformant';
  }
  if (checks.some((check) => check.status === 'partial')) {
    return 'partial';
  }
  return 'conformant';
}

function buildRecommendedAmendments(input: {
  trustDeltas: string[];
  governanceDeltas: string[];
  routingDeltas: string[];
  delegationFailures: string[];
  invariantViolations: string[];
  replayRegressions: string[];
  conformanceFailures: string[];
}): string[] {
  const amendments = new Set<string>();
  if (input.trustDeltas.length > 0) amendments.add('review trust algebra thresholds and weights');
  if (input.governanceDeltas.length > 0) amendments.add('review governance tier thresholds and policy clauses');
  if (input.routingDeltas.length > 0) amendments.add('review routing policy weighting and trust gating');
  if (input.delegationFailures.length > 0) amendments.add('review delegation chain law and authority thresholds');
  if (input.invariantViolations.length > 0) amendments.add('repair constitutional invariant set and amendment guardrails');
  if (input.replayRegressions.length > 0) amendments.add('require replay validation before adoption');
  if (input.conformanceFailures.length > 0) amendments.add('repair conformance rules across planes');
  return [...amendments];
}

function diffObjects(before: unknown, after: unknown, path = ''): GovernanceConfigDiff['changes'] {
  if (isPrimitive(before) || isPrimitive(after) || Array.isArray(before) || Array.isArray(after)) {
    if (stableJson(before) === stableJson(after)) {
      return [];
    }
    return [{
      path: path || '$',
      before,
      after,
    }];
  }

  const left = normalizeObject(before);
  const right = normalizeObject(after);
  const keys = new Set([...Object.keys(left), ...Object.keys(right)]);
  const changes: GovernanceConfigDiff['changes'] = [];
  for (const key of [...keys].sort()) {
    const nextPath = path ? `${path}.${key}` : key;
    if (!(key in left)) {
      changes.push({ path: nextPath, before: undefined, after: right[key] });
      continue;
    }
    if (!(key in right)) {
      changes.push({ path: nextPath, before: left[key], after: undefined });
      continue;
    }
    changes.push(...diffObjects(left[key], right[key], nextPath));
  }
  return changes;
}

function normalizeObject(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {};
  }
  return value as Record<string, unknown>;
}

function isPrimitive(value: unknown): boolean {
  return value === null || (typeof value !== 'object' && typeof value !== 'function');
}

function stableJson(value: unknown): string {
  return JSON.stringify(sortValue(value));
}

function sortValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(sortValue);
  }
  if (!value || typeof value !== 'object') {
    return value;
  }
  const sorted: Record<string, unknown> = {};
  for (const key of Object.keys(value as Record<string, unknown>).sort()) {
    const next = (value as Record<string, unknown>)[key];
    if (next !== undefined) {
      sorted[key] = sortValue(next);
    }
  }
  return sorted;
}

function hashCanonical(value: unknown): string {
  return crypto.createHash('sha256').update(JSON.stringify(sortValue(value))).digest('hex');
}

function clamp01(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.min(1, Math.max(0, value));
}
