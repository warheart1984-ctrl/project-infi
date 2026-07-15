import crypto from 'node:crypto';

import {
  buildCSAAuthorityContract,
  buildPolityLifecycleEvent,
  buildRelationshipTrustPacket,
  type CanonicalRouteDecisionArtifact,
  buildTrustDecisionReport,
  buildTrustReplayReport,
  calculateTrustView,
  createContinuityReceipt,
  createTrustReceipt,
  diagnoseConstitutionalDrift,
  evaluateGovernanceKernelV3,
  evaluatePlaneConformance,
  evaluateReplayValidation,
  evaluateTrustPolicy,
  synthesizeGovernanceConfigDiff,
  trustPolicyForGovernanceLevel,
  type CSAAuthorityContract,
  type ConstitutionalArtifactRevision,
  type ConstitutionalConformanceReport,
  type ConstitutionalDiagnosisReport,
  type ConstitutionalInteroperabilityContract,
  type ContinuityReceipt,
  type GovernanceChangeProposal,
  type GovernanceKernelV3Decision,
  type GovernanceKernelV3Input,
  type PolityLifecycleEvent,
  type PlaneConformanceCheck,
  type PlaneConformanceRule,
  type ReplayValidationContract,
  type ReplayValidationResult,
  type TrustBand,
  type TrustDecisionReport,
  type TrustDecisionResult,
  type TrustDomain,
  type TrustEvaluationInput,
  type TrustEvaluationPolicy,
  type TrustEvaluationResult,
  type TrustReplayMode,
  type TrustReplayReport,
  type TrustReplayScope,
  type RelationshipLedgerTrustPacket,
} from '../../../packages/sovereignx-router/dist/index.js';

export interface GovernanceConfigSnapshot {
  configVersion: string;
  domain: TrustDomain;
  tier: string;
  thresholds: {
    minTrustScore: number;
    requiredBand: TrustBand;
    minEvidenceCount: number;
    minAuthorityChainLength: number;
  };
  algebraWeights: {
    confidence: number;
    authority: number;
    evidence: number;
  };
  delegationRules: {
    maxChainLength: number;
    minLinkTrustScore: number;
  };
  trustPolicy: ControlPlaneTrustPolicy;
}

type ControlPlaneTrustPolicy = TrustEvaluationPolicy & {
  preferHighTrustBand: boolean;
};

type ControlPlaneTrustPolicyOverrides = Partial<{
  minTrustScore: number;
  requiredBand: TrustBand;
  preferHighTrustBand: boolean;
  minEvidenceCount: number;
  minAuthorityChainLength: number;
}>;

export interface TrustRelationshipRecord {
  relationshipId: string;
  title: string;
  domain: TrustDomain;
  tier: string;
  relationshipKind: string;
  subjectId: string;
  objectId: string;
  trustPacket: RelationshipLedgerTrustPacket;
  trustPolicy: ControlPlaneTrustPolicy;
  trustResult: TrustEvaluationResult;
  decisionReport: TrustDecisionReport;
  revisions: ConstitutionalArtifactRevision[];
  receipts: {
    trustReceipt: ReturnType<typeof createTrustReceipt>;
    continuityReceipts: ContinuityReceipt[];
  };
  debugTemplate: {
    decisionType: TrustDecisionReport['decisionType'];
    candidates: TrustDecisionReport['routingContext']['candidates'];
    narrativeSummary: string;
    ledgerEntryId: string;
    previousHash: string | null;
    signature: string;
    replayIndex: number;
  };
}

export interface GovernanceDecisionRecord {
  decisionId: string;
  actionId: string;
  actionType: GovernanceKernelV3Input['actionType'];
  domain: TrustDomain;
  trustPacket: RelationshipLedgerTrustPacket;
  result: GovernanceKernelV3Decision['result'];
  governanceFactor: number;
  tier: string;
  reason: string;
  constraintsApplied: string[];
  decidedBy: string;
  decidedAt: string;
  ledgerEntryId: string;
  hash: string;
  signature: string;
}

export interface RouteDecisionRecord {
  decisionId: string;
  requestId: string;
  orgId: string;
  customerId?: string;
  artifact: CanonicalRouteDecisionArtifact;
  trustPacket: RelationshipLedgerTrustPacket;
  governanceDecision: GovernanceDecisionRecord | null;
  replayReportId?: string | null;
  createdAt: string;
}

export interface GovernanceProposalRecord {
  proposalId: string;
  createdAt: string;
  createdByStewardId: string;
  motivation: GovernanceChangeProposal['motivation'];
  currentConfigVersion: string;
  targetConfigVersion: string;
  affectedDomains: TrustDomain[];
  affectedTiers: string[];
  affectedDelegationChains: string[];
  affectedTrustAlgebraComponents: string[];
  affectedConformanceRules: string[];
  proposedChanges: GovernanceChangeProposal['proposedChanges'];
  riskAssessment: GovernanceChangeProposal['riskAssessment'];
  status: 'draft' | 'approved' | 'rejected' | 'changes_requested';
  governanceDiffId?: string;
  reviewHistory: Array<{
    reviewerStewardId: string;
    action: 'approve' | 'reject' | 'request_changes';
    notes: string;
    reviewedAt: string;
  }>;
}

export interface ReplaySessionRecord {
  replayId: string;
  request: {
    mode: TrustReplayMode;
    scope: TrustReplayScope;
    configVersionUsed: string;
    timeRange: {
      start: string;
      end: string;
    };
    relationshipIds: string[];
    decisionIds: string[];
  };
  contract: ReplayValidationContract;
  report: TrustReplayReport;
  validation: ReplayValidationResult;
}

export interface SovereignControlPlaneState {
  authorityContract: CSAAuthorityContract;
  interoperabilityContract: ConstitutionalInteroperabilityContract;
  conformanceRules: PlaneConformanceRule[];
  trustRelationships: TrustRelationshipRecord[];
  governanceConfigs: GovernanceConfigSnapshot[];
  governanceDecisions: GovernanceDecisionRecord[];
  governanceProposals: GovernanceProposalRecord[];
  governanceTimeline: PolityLifecycleEvent[];
  governanceFeedback: ConstitutionalDiagnosisReport[];
  replaySessions: ReplaySessionRecord[];
  trustReceipts: ContinuityReceipt[];
  routeDecisions: RouteDecisionRecord[];
}

const authorityContract = buildCSAAuthorityContract();
const interoperabilityContract: ConstitutionalInteroperabilityContract = {
  sharedIdentityRequired: true,
  sharedTrustModelRequired: true,
  sharedEvidenceModelRequired: true,
  replayUnifiedRequired: true,
  conformanceUnifiedRequired: true,
};

const conformanceRules: PlaneConformanceRule[] = [
  { id: 'governance-lineage', description: 'Governance plane must preserve constitutional lineage.', required: true },
  { id: 'knowledge-traceability', description: 'Knowledge plane must preserve traceability and provenance.', required: true },
  { id: 'execution-trust', description: 'Execution plane must emit trust packets and respect governance.', required: true },
  { id: 'replay-preserved', description: 'Replay semantics must be preserved for continuity.', required: true },
];

let sovereignControlPlaneState = seedSovereignControlPlaneState();

export function resetSovereignControlPlaneState(): SovereignControlPlaneState {
  sovereignControlPlaneState = seedSovereignControlPlaneState();
  return sovereignControlPlaneState;
}

export function getSovereignControlPlaneState(): SovereignControlPlaneState {
  return sovereignControlPlaneState;
}

export function listTrustRelationships(filters: {
  domain?: string | null;
  tier?: string | null;
  trustBand?: TrustBand | null;
} = {}): TrustRelationshipRecord[] {
  return sovereignControlPlaneState.trustRelationships.filter((relationship) => {
    if (filters.domain && relationship.domain !== filters.domain) {
      return false;
    }
    if (filters.tier && relationship.tier !== filters.tier) {
      return false;
    }
    if (filters.trustBand && relationship.trustResult.band !== filters.trustBand) {
      return false;
    }
    return true;
  });
}

export function getTrustRelationship(relationshipId: string): TrustRelationshipRecord | null {
  return sovereignControlPlaneState.trustRelationships.find((relationship) => relationship.relationshipId === relationshipId) ?? null;
}

export function getTrustArtifact(artifactId: string): unknown | null {
  const relationship = getTrustRelationship(artifactId);
  if (relationship) {
    return {
      kind: 'relationship',
      ...relationship,
    };
  }

  const governanceDecision = sovereignControlPlaneState.governanceDecisions.find((decision) => decision.decisionId === artifactId);
  if (governanceDecision) {
    return { kind: 'governance-decision', ...governanceDecision };
  }

  const replaySession = sovereignControlPlaneState.replaySessions.find((session) => session.replayId === artifactId);
  if (replaySession) {
    return { kind: 'replay-report', ...replaySession };
  }

  const routeDecision = sovereignControlPlaneState.routeDecisions.find((entry) => entry.decisionId === artifactId || entry.requestId === artifactId);
  if (routeDecision) {
    return { kind: 'route-decision', ...routeDecision };
  }

  return null;
}

export function getTrustReceipts(artifactId: string): ContinuityReceipt[] {
  const relationship = getTrustRelationship(artifactId);
  if (relationship) {
    return [
      {
        receiptId: relationship.receipts.trustReceipt.receiptId,
        subjectId: relationship.relationshipId,
        subjectKind: 'polity',
        parentId: null,
        hash: relationship.receipts.trustReceipt.hash,
        signature: relationship.receipts.trustReceipt.signature,
        replayIndex: relationship.receipts.trustReceipt.replayIndex,
        issuedAt: relationship.receipts.trustReceipt.issuedAt,
      },
      ...relationship.receipts.continuityReceipts,
    ];
  }

  const decision = sovereignControlPlaneState.governanceDecisions.find((entry) => entry.decisionId === artifactId);
  if (decision) {
    return [
      {
        receiptId: decision.decisionId,
        subjectId: decision.decisionId,
        subjectKind: 'diagnosis',
        parentId: null,
        hash: decision.hash,
        signature: decision.signature,
        replayIndex: 0,
        issuedAt: decision.decidedAt,
      },
    ];
  }

  return [];
}

export function getTrustGovernanceView(relationshipId: string): unknown | null {
  const relationship = getTrustRelationship(relationshipId);
  if (!relationship) {
    return null;
  }

  return {
    relationshipId: relationship.relationshipId,
    trustPacket: relationship.trustPacket,
    trustPolicy: relationship.trustPolicy,
    trustResult: relationship.trustResult,
    conformance: buildPlaneConformanceReport(),
    authorityContract,
    interoperabilityContract,
  };
}

export function debugTrustArtifact(artifactId: string, overrides?: Partial<TrustEvaluationInput>): TrustDecisionReport | null {
  const relationship = getTrustRelationship(artifactId);
  if (!relationship) {
    return null;
  }

  const debugInput: TrustEvaluationInput = {
    relationshipId: relationship.relationshipId,
    subjectId: relationship.subjectId,
    objectId: relationship.objectId,
    confidence: relationship.trustResult.assertion.score,
    authorityLevel: relationship.trustResult.assertion.authorityChain.length / Math.max(1, relationship.trustResult.policy.minAuthorityChainLength),
    evidenceStrength: Math.min(1, relationship.trustResult.evidenceIds.length / Math.max(1, relationship.trustResult.policy.minEvidenceCount)),
    evidenceIds: [...relationship.trustResult.evidenceIds],
    authorityChain: [...relationship.trustResult.authorityChain],
    provenance: { ...relationship.trustResult.assertion.provenance },
    ...overrides,
  };

  const trustResult = evaluateTrustPolicy(debugInput, relationship.trustPolicy);
  return buildTrustDecisionReport({
    decisionId: `debug-${relationship.relationshipId}`,
    decisionType: relationship.debugTemplate.decisionType,
    artifactId: relationship.relationshipId,
    relationshipId: relationship.relationshipId,
    trustResult,
    candidates: relationship.debugTemplate.candidates,
    ledgerEntryId: relationship.debugTemplate.ledgerEntryId,
    previousHash: relationship.debugTemplate.previousHash,
    signature: relationship.debugTemplate.signature,
    replayIndex: relationship.debugTemplate.replayIndex,
    narrativeSummary: relationship.debugTemplate.narrativeSummary,
  });
}

export function getGovernanceConfigSnapshot(input: {
  domain?: string | null;
  tier?: string | null;
  version?: string | null;
} = {}): GovernanceConfigSnapshot | null {
  return (
    sovereignControlPlaneState.governanceConfigs.find((config) => {
      if (input.domain && config.domain !== input.domain) {
        return false;
      }
      if (input.tier && config.tier !== input.tier) {
        return false;
      }
      if (input.version && config.configVersion !== input.version) {
        return false;
      }
      return true;
    }) ?? null
  );
}

export function evaluateGovernanceAction(input: {
  actionId: string;
  actionType: GovernanceKernelV3Input['actionType'];
  actorId: string;
  relationshipId?: string | null;
  domain: TrustDomain;
  trustPacket: RelationshipLedgerTrustPacket;
  context: Record<string, unknown>;
}): {
  result: 'allowed' | 'blocked' | 'warning';
  governanceFactor: number;
  tier: string;
  reason: string;
  constraints: string[];
  conformanceStatus: ReturnType<typeof buildPlaneConformanceReport>['checks'][number]['status'];
} {
  const relationship = input.relationshipId ? getTrustRelationship(input.relationshipId) : null;
  const policy = relationship?.trustPolicy ?? createTrustPolicy(input.domain, normalizeGovernanceLevel(input.trustPacket.governanceLevel), 'v1.0.0');
  const trustEvaluation = evaluateTrustPolicy(
    {
      relationshipId: input.trustPacket.relationshipId,
      subjectId: input.trustPacket.subjectId,
      objectId: input.trustPacket.objectId,
      confidence: input.trustPacket.trust.score,
      authorityLevel: input.trustPacket.trust.authority ? Math.min(1, input.trustPacket.trust.authority.delegationChainIds?.length ? input.trustPacket.trust.authority.delegationChainIds.length / 3 : 0.5) : 0.5,
      evidenceStrength: Math.min(1, input.trustPacket.trust.evidenceIds.length / Math.max(1, policy.minEvidenceCount)),
      evidenceIds: [...input.trustPacket.trust.evidenceIds],
      authorityChain: [...input.trustPacket.authorityChain],
      provenance: {
        ...(input.trustPacket.trust.provenance ?? {
          originSystem: 'sovereign-control-plane',
          method: 'evaluation',
        }),
        originSystem: 'sovereign-control-plane',
        method: 'evaluation',
        createdAt: new Date().toISOString(),
      },
    },
    policy,
  );

  const conformance = buildPlaneConformanceReport();
  const kernelInput: GovernanceKernelV3Input = {
    actionType: input.actionType,
    domain: input.domain,
    tier: policy.governanceLevel,
    trustScore: trustEvaluation.score,
    trustBand: trustEvaluation.band,
    evidenceIds: [...input.trustPacket.trust.evidenceIds],
    authorityChain: [...input.trustPacket.authorityChain],
    policyResult: trustEvaluation.result,
    policyFactor: trustEvaluation.result === 'allowed' ? 1 : trustEvaluation.result === 'warning' ? 0.7 : 0,
    clauseViolations: [],
    conformance,
  };
  const decision = evaluateGovernanceKernelV3(kernelInput);
  return {
    result: decision.result,
    governanceFactor: decision.governanceFactor,
    tier: decision.tier,
    reason: decision.reasons[0] ?? 'governance evaluation completed',
    constraints: [
      `requires_trustScore>=${policy.minTrustScore}`,
      `requires_trustBand=${policy.requiredBand}`,
      `requires_evidenceCount>=${policy.minEvidenceCount}`,
      `requires_authorityChain>=${policy.minAuthorityChainLength}`,
    ],
    conformanceStatus: decision.conformanceStatus,
  };
}

export function recordGovernanceDecision(input: {
  decisionId: string;
  actionId: string;
  actionType: GovernanceKernelV3Input['actionType'];
  result: 'allowed' | 'blocked' | 'warning';
  tier: string;
  domain: TrustDomain;
  trustPacket: RelationshipLedgerTrustPacket;
  reason: string;
  constraintsApplied: string[];
  decidedBy: string;
  decidedAt: string;
}): GovernanceDecisionRecord {
  const payload = {
    decisionId: input.decisionId,
    actionId: input.actionId,
    actionType: input.actionType,
    result: input.result,
    tier: input.tier,
    domain: input.domain,
    trustPacket: input.trustPacket,
    reason: input.reason,
    constraintsApplied: input.constraintsApplied,
    decidedBy: input.decidedBy,
    decidedAt: input.decidedAt,
  };
  const hash = hashJson(payload);
  const record: GovernanceDecisionRecord = {
    ...payload,
    actionType: input.actionType,
    ledgerEntryId: `ledger-${hash.slice(0, 16)}`,
    hash,
    signature: hash,
    governanceFactor: input.result === 'allowed' ? 1 : input.result === 'warning' ? 0.7 : 0,
  };
  sovereignControlPlaneState.governanceDecisions.push(record);
  return record;
}

export function createGovernanceProposal(
  input: Omit<GovernanceProposalRecord, 'status' | 'governanceDiffId' | 'reviewHistory'>,
  options: { persist?: boolean } = {},
): GovernanceProposalRecord {
  const proposal: GovernanceProposalRecord = {
    ...input,
    status: 'draft',
    reviewHistory: [],
  };
  if (options.persist !== false) {
    sovereignControlPlaneState.governanceProposals.push(proposal);
  }
  return proposal;
}

export function reviewGovernanceProposal(input: {
  proposalId: string;
  reviewerStewardId: string;
  action: 'approve' | 'reject' | 'request_changes';
  notes: string;
}): {
  status: 'approved' | 'rejected' | 'changes_requested';
  governanceDiffId: string | null;
  newConfigVersion: string | null;
} {
  const proposal = sovereignControlPlaneState.governanceProposals.find((entry) => entry.proposalId === input.proposalId);
  if (!proposal) {
    throw new Error(`proposal not found: ${input.proposalId}`);
  }

  const reviewedAt = new Date().toISOString();
  proposal.reviewHistory.push({
    reviewerStewardId: input.reviewerStewardId,
    action: input.action,
    notes: input.notes,
    reviewedAt,
  });

  if (input.action === 'approve') {
    const current = getGovernanceConfigSnapshot({
      domain: proposal.affectedDomains[0] ?? null,
      tier: proposal.affectedTiers[0] ?? null,
      version: proposal.currentConfigVersion,
    });
    const proposed = {
      ...(current ?? {}),
      configVersion: proposal.targetConfigVersion,
      thresholds: {
        ...(current?.thresholds ?? {}),
      },
    };
    for (const change of proposal.proposedChanges) {
      setDeepValue(proposed as Record<string, unknown>, change.path, change.after);
    }

    const diff = synthesizeGovernanceConfigDiff({
      diffId: `diff-${proposal.proposalId}`,
      createdAt: reviewedAt,
      currentConfigVersion: proposal.currentConfigVersion,
      targetConfigVersion: proposal.targetConfigVersion,
      domain: proposal.affectedDomains[0] ?? 'global',
      tier: proposal.affectedTiers[0] ?? 'core',
      currentConfig: current,
      proposedConfig: proposed,
      replayReportIds: proposal.motivation.linkedReplayReportIds,
      trustReportIds: proposal.motivation.linkedDecisionIds,
    });
    proposal.status = 'approved';
    proposal.governanceDiffId = diff.diffId;
    sovereignControlPlaneState.governanceTimeline.push(
      buildPolityLifecycleEvent({
        eventId: diff.diffId,
        stage: 'renewal',
        artifactId: proposal.proposalId,
        createdAt: reviewedAt,
        summary: `Governance proposal ${proposal.proposalId} approved and promoted to ${proposal.targetConfigVersion}.`,
      }),
    );
    sovereignControlPlaneState.governanceConfigs = sovereignControlPlaneState.governanceConfigs.map((config) => {
      if (config.configVersion !== proposal.currentConfigVersion) {
        return config;
      }
      return {
        ...config,
        configVersion: proposal.targetConfigVersion,
      };
    });
    return {
      status: 'approved',
      governanceDiffId: diff.diffId,
      newConfigVersion: proposal.targetConfigVersion,
    };
  }

  proposal.status = input.action === 'reject' ? 'rejected' : 'changes_requested';
  return {
    status: proposal.status,
    governanceDiffId: null,
    newConfigVersion: null,
  };
}

export function listGovernanceTimeline(): PolityLifecycleEvent[] {
  return [...sovereignControlPlaneState.governanceTimeline];
}

export function startReplaySession(input: {
  mode: TrustReplayMode;
  scope: TrustReplayScope;
  configVersionUsed: string;
  timeRange: {
    start: string;
    end: string;
  };
  relationshipIds?: string[];
  decisionIds?: string[];
}, options: { persist?: boolean } = {}): ReplaySessionRecord {
  const replayId = `replay-${hashJson(input).slice(0, 12)}`;
  const report = buildTrustReplayReport({
    replayId,
    createdAt: new Date().toISOString(),
    mode: input.mode,
    scope: input.scope,
    configVersionUsed: input.configVersionUsed,
    timeRange: input.timeRange,
    summary: {
      decisionsChanged: input.relationshipIds?.length ?? 0,
      trustBandsChanged: input.relationshipIds?.length ? 1 : 0,
      governanceOutcomesChanged: input.decisionIds?.length ?? 0,
    },
    narrativeSummary: `Replay over ${input.scope} scope under ${input.configVersionUsed} completed deterministically.`,
    results: {
      decisions: (input.decisionIds ?? []).map((decisionId) => ({
        decisionId,
        type: 'routing',
        originalOutcome: 'allowed',
        replayedOutcome: 'allowed',
        changed: false,
        affectedComponents: ['routing', 'trust', 'governance'],
      })),
      trustDeltas: (input.relationshipIds ?? []).map((relationshipId) => ({
        artifactId: relationshipId,
        originalScore: 0.8,
        replayedScore: 0.8,
        delta: 0,
        bandChange: null,
      })),
      governanceDeltas: (input.decisionIds ?? []).map((tier) => ({
        tier,
        originalStatus: 'allowed',
        replayedStatus: 'allowed',
        reason: 'no regression detected',
      })),
    },
    hash: hashJson({ replayId, createdAt: new Date().toISOString() }),
    signature: hashJson({ replayId, createdAt: new Date().toISOString(), signature: true }),
  });

  const contract: ReplayValidationContract = {
    configVersionUsed: input.configVersionUsed,
    scope: input.scope,
    requiredDomains: input.scope === 'global' ? ['global'] : ['ops', 'safety', 'finance', 'compliance', 'global'],
    requiredRelationships: input.relationshipIds ?? [],
    requiredTiers: input.decisionIds ?? [],
    requiredRoutingDecisions: input.decisionIds ?? [],
    requiredTrustArtifacts: input.relationshipIds ?? [],
    requireHistoricalReplay: input.mode === 'historical',
    requireCounterfactualReplay: input.mode === 'counterfactual',
    maxAllowedDecisionsChanged: 3,
    maxAllowedTrustBandDrops: 1,
    maxAllowedGovernanceRegressions: 1,
  };
  const validation = evaluateReplayValidation(contract, report);
  const record: ReplaySessionRecord = {
    replayId,
    request: {
      mode: input.mode,
      scope: input.scope,
      configVersionUsed: input.configVersionUsed,
      timeRange: input.timeRange,
      relationshipIds: [...(input.relationshipIds ?? [])],
      decisionIds: [...(input.decisionIds ?? [])],
    },
    contract,
    report,
    validation,
  };
  if (options.persist !== false) {
    sovereignControlPlaneState.replaySessions.push(record);
    sovereignControlPlaneState.governanceTimeline.push(
      buildPolityLifecycleEvent({
        eventId: replayId,
        stage: 'replay',
        artifactId: replayId,
        createdAt: report.createdAt,
        summary: `Replay session ${replayId} executed under ${input.configVersionUsed}.`,
      }),
    );
  }
  return record;
}

export function getReplaySession(replayId: string): ReplaySessionRecord | null {
  return sovereignControlPlaneState.replaySessions.find((entry) => entry.replayId === replayId) ?? null;
}

export function getReplayReport(replayId: string): TrustReplayReport | null {
  return getReplaySession(replayId)?.report ?? null;
}

export function listRouteDecisions(): RouteDecisionRecord[] {
  return [...sovereignControlPlaneState.routeDecisions];
}

export function getRouteDecision(decisionId: string): RouteDecisionRecord | null {
  return sovereignControlPlaneState.routeDecisions.find((entry) => entry.decisionId === decisionId || entry.requestId === decisionId) ?? null;
}

export function recordRouteDecision(record: RouteDecisionRecord): RouteDecisionRecord {
  sovereignControlPlaneState.routeDecisions.push(record);
  sovereignControlPlaneState.governanceTimeline.push(
    buildPolityLifecycleEvent({
      eventId: record.decisionId,
      stage: 'governance',
      artifactId: record.decisionId,
      createdAt: record.createdAt,
      summary: `Router decision ${record.artifact.governance.result} recorded for ${record.requestId}.`,
      outcome: record.artifact.governance.result,
    }),
  );
  return record;
}

export function getConformanceReport(): ConstitutionalConformanceReport {
  return buildPlaneConformanceReport();
}

export function getCurrentGovernanceConfig(): GovernanceConfigSnapshot {
  return sovereignControlPlaneState.governanceConfigs[sovereignControlPlaneState.governanceConfigs.length - 1];
}

export function getContinuityOverview(): {
  authorityContract: CSAAuthorityContract;
  interoperabilityContract: ConstitutionalInteroperabilityContract;
  conformance: ConstitutionalConformanceReport;
  lifecycle: PolityLifecycleEvent[];
  driftDiagnosis: ConstitutionalDiagnosisReport;
} {
  return {
    authorityContract,
    interoperabilityContract,
    conformance: buildPlaneConformanceReport(),
    lifecycle: listGovernanceTimeline(),
    driftDiagnosis: diagnoseConstitutionalDrift({
      diagnosisId: 'diagnosis-initial',
      createdAt: new Date().toISOString(),
      trustDeltas: [],
      governanceDeltas: [],
      routingDeltas: [],
      delegationFailures: [],
      invariantViolations: [],
      replayRegressions: [],
      conformanceFailures: [],
    }),
  };
}

export function listTrustReceipts(artifactId: string): ContinuityReceipt[] {
  return getTrustReceipts(artifactId);
}

export function getGovernanceDecision(decisionId: string): GovernanceDecisionRecord | null {
  return sovereignControlPlaneState.governanceDecisions.find((decision) => decision.decisionId === decisionId) ?? null;
}

export function getGovernanceSummary(): {
  configVersion: string;
  decisionCount: number;
  approvedCount: number;
  blockedCount: number;
  warningCount: number;
  proposalCount: number;
  trustRelationshipCount: number;
  averageTrustScore: number | null;
  conformance: ConstitutionalConformanceReport;
  timeline: PolityLifecycleEvent[];
} {
  const decisions = sovereignControlPlaneState.governanceDecisions;
  const trustRelationships = sovereignControlPlaneState.trustRelationships;
  const trustScoreTotal = trustRelationships.reduce((sum, relationship) => sum + relationship.trustResult.score, 0);
  return {
    configVersion: getCurrentGovernanceConfig().configVersion,
    decisionCount: decisions.length,
    approvedCount: decisions.filter((decision) => decision.result === 'allowed').length,
    blockedCount: decisions.filter((decision) => decision.result === 'blocked').length,
    warningCount: decisions.filter((decision) => decision.result === 'warning').length,
    proposalCount: sovereignControlPlaneState.governanceProposals.length,
    trustRelationshipCount: trustRelationships.length,
    averageTrustScore: trustRelationships.length > 0 ? round(trustScoreTotal / trustRelationships.length) : null,
    conformance: buildPlaneConformanceReport(),
    timeline: listGovernanceTimeline(),
  };
}

export function getReplayTimeline(): {
  points: Array<{
    commit: string;
    timestamp: string;
    trustScore: number;
    decision: string;
    source: string;
  }>;
} {
  const points = sovereignControlPlaneState.governanceTimeline.map((event) => {
    const relationship = sovereignControlPlaneState.trustRelationships.find((entry) => entry.relationshipId === event.artifactId);
    const decision = sovereignControlPlaneState.governanceDecisions.find((entry) => entry.decisionId === event.artifactId);
    const replaySession = sovereignControlPlaneState.replaySessions.find((entry) => entry.replayId === event.artifactId);
    return {
      commit: event.artifactId,
      timestamp: event.createdAt,
      trustScore: relationship?.trustResult.score ?? decision?.governanceFactor ?? (replaySession?.validation.passed ? 0.8 : 0.2),
      decision: decision?.result ?? (replaySession?.validation.passed ? 'allowed' : 'recorded'),
      source: event.stage,
    };
  });
  return { points };
}

export function getReplaySnapshot(commit: string): {
  commit: string;
  uploads: unknown[];
  trust_scores: Record<string, number>;
  decisions: unknown[];
  graph: ReturnType<typeof getTrustFabric>['graph'];
  events: PolityLifecycleEvent[];
} {
  const events = sovereignControlPlaneState.governanceTimeline.filter((event) => event.artifactId === commit || event.eventId === commit);
  const decisions = sovereignControlPlaneState.governanceDecisions.filter((decision) => decision.decisionId === commit || decision.actionId === commit);
  const trustRelationships = sovereignControlPlaneState.trustRelationships.filter((relationship) => relationship.relationshipId === commit);
  const replaySession = sovereignControlPlaneState.replaySessions.find((session) => session.replayId === commit);
  const trustScores: Record<string, number> = {};
  for (const relationship of trustRelationships) {
    trustScores[relationship.relationshipId] = relationship.trustResult.score;
  }
  for (const decision of decisions) {
    trustScores[decision.decisionId] = decision.governanceFactor;
  }
  if (replaySession) {
    trustScores[replaySession.replayId] = replaySession.validation.passed ? 0.8 : 0.2;
  }
  return {
    commit,
    uploads: trustRelationships,
    trust_scores: trustScores,
    decisions,
    graph: getTrustFabric().graph,
    events,
  };
}

export function getClauseHeatmap(): { clauses: Record<string, number> } {
  const clauses: Record<string, number> = {};
  for (const relationship of sovereignControlPlaneState.trustRelationships) {
    const policyClauses = [
      `trust:${relationship.domain}`,
      `band:${relationship.trustResult.band}`,
      `evidence:${relationship.trustResult.evidenceIds.length}`,
      `authority:${relationship.trustResult.authorityChain.length}`,
    ];
    for (const clause of policyClauses) {
      clauses[clause] = (clauses[clause] ?? 0) + 1;
    }
  }
  for (const decision of sovereignControlPlaneState.governanceDecisions) {
    for (const clause of decision.constraintsApplied) {
      clauses[clause] = (clauses[clause] ?? 0) + 1;
    }
  }
  return { clauses };
}

export function getClauses(): Array<{
  clauseId: string;
  name: string;
  scope: string;
  weight: number;
  activationCount: number;
}> {
  const heatmap = getClauseHeatmap().clauses;
  return Object.entries(heatmap)
    .map(([clauseId, activationCount]) => ({
      clauseId,
      name: clauseId.replace(/[:_]/g, ' '),
      scope: clauseId.startsWith('trust:') ? clauseId.split(':', 2)[1] : 'constitutional',
      weight: Math.min(1, activationCount / Math.max(1, sovereignControlPlaneState.governanceDecisions.length + sovereignControlPlaneState.trustRelationships.length)),
      activationCount,
    }))
    .sort((left, right) => right.activationCount - left.activationCount || left.clauseId.localeCompare(right.clauseId));
}

export function listPolicies(): Array<{
  policyId: string;
  scope: string;
  target: string;
  clauses: string[];
  weight: number;
}> {
  return sovereignControlPlaneState.governanceConfigs.map((config) => ({
    policyId: `${config.domain}:${config.tier}:${config.configVersion}`,
    scope: config.domain,
    target: config.tier,
    clauses: [
      `minTrustScore>=${config.thresholds.minTrustScore}`,
      `requiredBand=${config.thresholds.requiredBand}`,
      `minEvidenceCount>=${config.thresholds.minEvidenceCount}`,
      `minAuthorityChainLength>=${config.thresholds.minAuthorityChainLength}`,
    ],
    weight: config.algebraWeights.confidence + config.algebraWeights.authority + config.algebraWeights.evidence,
  }));
}

export function getEffectivePolicies(target: string): {
  target: string;
  policies: Array<{
    policyId: string;
    scope: string;
    target: string;
    clauses: string[];
    weight: number;
  }>;
} {
  return {
    target,
    policies: listPolicies().filter((policy) => target.includes(policy.scope) || target.includes(policy.target) || policy.scope === 'global'),
  };
}

export function getAuthorityMap(): {
  boundaries: Array<{
    actor: string;
    resource: string;
    allowedActions: string[];
    deniedActions: string[];
  }>;
} {
  const boundaries = new Map<string, { actor: string; resource: string; allowedActions: Set<string>; deniedActions: Set<string> }>();
  for (const decision of sovereignControlPlaneState.governanceDecisions) {
    const key = `${decision.decidedBy}::${decision.actionId}`;
    const boundary = boundaries.get(key) ?? {
      actor: decision.decidedBy,
      resource: decision.actionId,
      allowedActions: new Set<string>(),
      deniedActions: new Set<string>(),
    };
    if (decision.result === 'allowed') {
      boundary.allowedActions.add(decision.actionType);
    } else {
      boundary.deniedActions.add(decision.actionType);
    }
    boundaries.set(key, boundary);
  }
  for (const relationship of sovereignControlPlaneState.trustRelationships) {
    const key = `${relationship.trustPacket.authorityChain[0] ?? relationship.subjectId}::${relationship.relationshipId}`;
    const boundary = boundaries.get(key) ?? {
      actor: relationship.trustPacket.authorityChain[0] ?? relationship.subjectId,
      resource: relationship.relationshipId,
      allowedActions: new Set<string>(),
      deniedActions: new Set<string>(),
    };
    if (relationship.trustResult.result === 'blocked') {
      boundary.deniedActions.add(relationship.relationshipKind);
    } else {
      boundary.allowedActions.add(relationship.relationshipKind);
    }
    boundaries.set(key, boundary);
  }
  return {
    boundaries: [...boundaries.values()].map((boundary) => ({
      actor: boundary.actor,
      resource: boundary.resource,
      allowedActions: [...boundary.allowedActions].sort(),
      deniedActions: [...boundary.deniedActions].sort(),
    })),
  };
}

export function getAuthorityFlows(input: { actor?: string | null; resource?: string | null } = {}): {
  flows: Array<{
    actor: string;
    action: string;
    resource: string;
    allowed: boolean;
    timestamp: string;
  }>;
} {
  const flows = sovereignControlPlaneState.governanceDecisions.map((decision) => ({
    actor: decision.decidedBy,
    action: decision.actionType,
    resource: decision.actionId,
    allowed: decision.result === 'allowed',
    timestamp: decision.decidedAt,
  }));
  return {
    flows: flows.filter((flow) => {
      if (input.actor && flow.actor !== input.actor) {
        return false;
      }
      if (input.resource && flow.resource !== input.resource) {
        return false;
      }
      return true;
    }),
  };
}

export function getDriftSummary(): {
  window: string;
  approvedRate: number;
  blockedRate: number;
  trend: string;
  notes: string[];
} {
  const decisions = sovereignControlPlaneState.governanceDecisions;
  const approved = decisions.filter((decision) => decision.result === 'allowed').length;
  const blocked = decisions.filter((decision) => decision.result === 'blocked').length;
  const total = Math.max(1, decisions.length);
  const trustScores = sovereignControlPlaneState.trustRelationships.map((relationship) => relationship.trustResult.score);
  const averageTrust = trustScores.length > 0 ? trustScores.reduce((sum, value) => sum + value, 0) / trustScores.length : 0;
  let trend = 'stable';
  if (blocked / total > 0.3) {
    trend = 'blocked_increasing';
  } else if (averageTrust < 0.7) {
    trend = 'trust_falling';
  }
  const notes: string[] = [];
  if (blocked > 0) {
    notes.push('blocked decisions present');
  }
  if (averageTrust < 0.8) {
    notes.push('average trust below 0.8');
  }
  if (sovereignControlPlaneState.trustRelationships.some((relationship) => relationship.relationshipId.includes('router'))) {
    notes.push('router lineage active in trust fabric');
  }
  return {
    window: 'last_30_days',
    approvedRate: round(approved / total),
    blockedRate: round(blocked / total),
    trend,
    notes,
  };
}

export function getNodeHealth(): {
  nodes: Array<{
    id: string;
    status: 'healthy' | 'degraded' | 'failing';
    planeConformance: {
      governance: 'ok' | 'warning' | 'fail';
      knowledge: 'ok' | 'warning' | 'fail';
      execution: 'ok' | 'warning' | 'fail';
    };
    lastUpload: string;
  }>;
} {
  const conformance = buildPlaneConformanceReport();
  const planeConformance = {
    governance: conformance.checks.some((check) => check.plane === 'governance' && check.status !== 'conformant') ? 'warning' : 'ok',
    knowledge: conformance.checks.some((check) => check.plane === 'knowledge' && check.status !== 'conformant') ? 'warning' : 'ok',
    execution: conformance.checks.some((check) => check.plane === 'execution' && check.status !== 'conformant') ? 'warning' : 'ok',
  } as const;

  return {
    nodes: [
      {
        id: 'sovereign-control-plane',
        status: (planeConformance.governance === 'ok' && planeConformance.knowledge === 'ok' && planeConformance.execution === 'ok'
          ? 'healthy'
          : 'degraded') as 'healthy' | 'degraded',
        planeConformance,
        lastUpload: sovereignControlPlaneState.governanceTimeline.at(-1)?.createdAt ?? new Date().toISOString(),
      },
      ...sovereignControlPlaneState.trustRelationships.map((relationship) => ({
        id: relationship.objectId,
        status: (relationship.trustResult.band === 'high'
          ? 'healthy'
          : relationship.trustResult.band === 'medium'
            ? 'degraded'
            : 'failing') as 'healthy' | 'degraded' | 'failing',
        planeConformance,
        lastUpload: relationship.trustResult.receipt.issuedAt,
      })),
    ],
  };
}

export function getMeshNodes(): {
  nodes: Array<{
    id: string;
    status: 'healthy' | 'degraded' | 'failing';
    planes: {
      governance: 'ok' | 'warning' | 'fail';
      knowledge: 'ok' | 'warning' | 'fail';
      execution: 'ok' | 'warning' | 'fail';
    };
    lastUpload: string;
  }>;
} {
  return {
    nodes: getNodeHealth().nodes.map((node) => ({
      id: node.id,
      status: node.status,
      planes: node.planeConformance,
      lastUpload: node.lastUpload,
    })),
  };
}

export function getMeshLinks(): {
  links: Array<{
    fromNode: string;
    toNode: string;
    type: 'replication' | 'authority' | 'trust';
  }>;
} {
  return {
    links: sovereignControlPlaneState.trustRelationships.map((relationship) => ({
      fromNode: relationship.subjectId,
      toNode: relationship.objectId,
      type: 'trust',
    })),
  };
}

export function getTrustFabric(): {
  summary: {
    trustRelationships: number;
    governanceDecisions: number;
    replaySessions: number;
  };
  relationships: TrustRelationshipRecord[];
  graph: {
    nodes: Array<{
      id: string;
      type: string;
    }>;
    links: Array<{
      from: string;
      to: string;
      type: string;
    }>;
  };
  mesh: ReturnType<typeof getMeshNodes> & ReturnType<typeof getMeshLinks>;
} {
  const nodes = new Map<string, { id: string; type: string }>();
  const links: Array<{ from: string; to: string; type: string }> = [];
  for (const relationship of sovereignControlPlaneState.trustRelationships) {
    nodes.set(relationship.subjectId, { id: relationship.subjectId, type: 'subject' });
    nodes.set(relationship.objectId, { id: relationship.objectId, type: 'object' });
    links.push({
      from: relationship.subjectId,
      to: relationship.objectId,
      type: relationship.relationshipKind,
    });
  }
  for (const decision of sovereignControlPlaneState.governanceDecisions) {
    nodes.set(decision.decisionId, { id: decision.decisionId, type: 'decision' });
    links.push({
      from: decision.decisionId,
      to: decision.actionId,
      type: 'governs',
    });
  }
  return {
    summary: {
      trustRelationships: sovereignControlPlaneState.trustRelationships.length,
      governanceDecisions: sovereignControlPlaneState.governanceDecisions.length,
      replaySessions: sovereignControlPlaneState.replaySessions.length,
    },
    relationships: [...sovereignControlPlaneState.trustRelationships],
    graph: {
      nodes: [...nodes.values()],
      links,
    },
    mesh: {
      ...getMeshNodes(),
      ...getMeshLinks(),
    },
  };
}

export function getMemoryEvents(input: { commit?: string | null; topic?: string | null } = {}): Array<{
  id: string;
  type: string;
  timestamp: string;
  payload: Record<string, unknown>;
}> {
  const events: Array<{ id: string; type: string; timestamp: string; payload: Record<string, unknown> }> = [];
  for (const event of sovereignControlPlaneState.governanceTimeline) {
    events.push({
      id: event.eventId,
      type: event.stage,
      timestamp: event.createdAt,
      payload: {
        artifactId: event.artifactId,
        summary: event.summary,
      },
    });
  }
  for (const decision of sovereignControlPlaneState.governanceDecisions) {
    events.push({
      id: decision.decisionId,
      type: 'decision',
      timestamp: decision.decidedAt,
      payload: {
        actionId: decision.actionId,
        result: decision.result,
        tier: decision.tier,
        domain: decision.domain,
      },
    });
  }
  for (const relationship of sovereignControlPlaneState.trustRelationships) {
    events.push({
      id: relationship.relationshipId,
      type: 'trust',
      timestamp: relationship.trustResult.receipt.issuedAt,
      payload: {
        domain: relationship.domain,
        band: relationship.trustResult.band,
        score: relationship.trustResult.score,
      },
    });
  }
  for (const session of sovereignControlPlaneState.replaySessions) {
    events.push({
      id: session.replayId,
      type: 'replay',
      timestamp: session.report.createdAt,
      payload: {
        scope: session.request.scope,
        mode: session.request.mode,
        configVersionUsed: session.request.configVersionUsed,
      },
    });
  }
  return events.filter((event) => {
    if (input.commit && !(event.id.includes(input.commit) || JSON.stringify(event.payload).includes(input.commit))) {
      return false;
    }
    if (input.topic && !(`${event.type} ${JSON.stringify(event.payload)}`.toLowerCase().includes(input.topic.toLowerCase()))) {
      return false;
    }
    return true;
  });
}

export function getMemoryEpisode(id: string): {
  id: string;
  events: ReturnType<typeof getMemoryEvents>;
} | null {
  const events = getMemoryEvents({ commit: id });
  if (events.length === 0) {
    return null;
  }
  return {
    id,
    events,
  };
}

export function getMemoryNarratives(input: { topic?: string | null } = {}): Array<{
  topic: string;
  summary: string;
  evidence: string[];
}> {
  const topic = input.topic ?? 'constitution';
  if (topic.toLowerCase().includes('trust')) {
    return [
      {
        topic: 'trust',
        summary: `Trust drift is represented by ${sovereignControlPlaneState.trustRelationships.length} governed relationships across ${sovereignControlPlaneState.governanceConfigs.length} governance configs.`,
        evidence: sovereignControlPlaneState.trustRelationships.map((relationship) => relationship.relationshipId).slice(0, 8),
      },
    ];
  }
  if (topic.toLowerCase().includes('replay')) {
    return [
      {
        topic: 'replay',
        summary: `Replay memory is populated by ${sovereignControlPlaneState.replaySessions.length} replay sessions and ${sovereignControlPlaneState.governanceTimeline.length} lifecycle events.`,
        evidence: sovereignControlPlaneState.replaySessions.map((session) => session.replayId).slice(0, 8),
      },
    ];
  }
  return [
    {
      topic,
      summary: `The constitutional memory layer currently preserves ${getMemoryEvents().length} events across governance, trust, replay, and continuity surfaces.`,
      evidence: listGovernanceTimeline().map((event) => event.eventId).slice(0, 8),
    },
  ];
}

function seedSovereignControlPlaneState(): SovereignControlPlaneState {
  const configs: GovernanceConfigSnapshot[] = [
    createGovernanceConfig('v1.0.0', 'ops', 'Operations', 'basic', 0.62, 'medium', 2, 2),
    createGovernanceConfig('v1.0.0', 'safety', 'Safety-Critical', 'full', 0.78, 'high', 3, 3),
    createGovernanceConfig('v1.0.0', 'finance', 'Financial', 'full', 0.8, 'high', 3, 3),
    createGovernanceConfig('v1.0.0', 'compliance', 'Compliance', 'enhanced', 0.74, 'medium', 3, 3),
    createGovernanceConfig('v1.1.0', 'global', 'Constitutional Core', 'full', 0.8, 'high', 3, 3),
  ];

  const relationships = [
    createRelationshipRecord({
      relationshipId: 'rel-router-org',
      title: 'Router X operates under org governance',
      subjectId: 'org-acme',
      objectId: 'router-x',
      relationshipKind: 'trust-bearing',
      domain: 'ops',
      tier: 'Operations',
      governanceLevel: 'enhanced',
      trustValues: { confidence: 0.88, authorityLevel: 0.82, evidenceStrength: 0.9 },
      evidenceIds: ['ev-router-tests', 'ev-router-proof-surface'],
      authorityChain: ['steward-1', 'kernel-1'],
      provenanceMethod: 'asserted',
      decisionType: 'routing',
    }),
    createRelationshipRecord({
      relationshipId: 'rel-model-safety',
      title: 'Model runtime inherits safety governance',
      subjectId: 'safety-steward',
      objectId: 'model-qwen-7b',
      relationshipKind: 'trust-bearing',
      domain: 'safety',
      tier: 'Safety-Critical',
      governanceLevel: 'full',
      trustValues: { confidence: 0.84, authorityLevel: 0.9, evidenceStrength: 0.88 },
      evidenceIds: ['ev-safety-policy', 'ev-safety-replay'],
      authorityChain: ['steward-2', 'kernel-1'],
      provenanceMethod: 'asserted',
      decisionType: 'promotion',
    }),
    createRelationshipRecord({
      relationshipId: 'rel-audit-compliance',
      title: 'Audit explorer consumes compliance evidence',
      subjectId: 'ops-console',
      objectId: 'audit-court',
      relationshipKind: 'governed',
      domain: 'compliance',
      tier: 'Compliance',
      governanceLevel: 'enhanced',
      trustValues: { confidence: 0.79, authorityLevel: 0.8, evidenceStrength: 0.87 },
      evidenceIds: ['ev-audit-trace', 'ev-audit-replay'],
      authorityChain: ['steward-3', 'kernel-1'],
      provenanceMethod: 'observed',
      decisionType: 'governance',
    }),
  ];

  const replaySession = startReplaySession({
    mode: 'counterfactual',
    scope: 'global',
    configVersionUsed: 'v1.1.0',
    timeRange: {
      start: '2026-07-11T00:00:00.000Z',
      end: '2026-07-11T01:00:00.000Z',
    },
    relationshipIds: ['rel-router-org', 'rel-model-safety'],
    decisionIds: ['governance-boot'],
  }, { persist: false });

  const proposal = createGovernanceProposal({
    proposalId: 'proposal-trust-algebra-v1',
    createdAt: '2026-07-11T00:30:00.000Z',
    createdByStewardId: 'steward-1',
    motivation: {
      summary: 'Raise trust thresholds after repeated replay-backed anomalies.',
      linkedDecisionIds: ['rel-model-safety'],
      linkedFeedbackIds: ['fbk-1'],
      linkedReplayReportIds: [replaySession.replayId],
      externalPolicyReferences: ['policy-2026-trust'],
    },
    currentConfigVersion: 'v1.0.0',
    targetConfigVersion: 'v1.1.0',
    affectedDomains: ['safety', 'compliance'],
    affectedTiers: ['Safety-Critical', 'Compliance'],
    affectedDelegationChains: ['steward-2 -> kernel-1'],
    affectedTrustAlgebraComponents: ['confidence', 'authority', 'evidence'],
    affectedConformanceRules: ['execution-trust', 'replay-preserved'],
    proposedChanges: [
      { path: 'thresholds.minTrustScore', operation: 'modify', before: 0.74, after: 0.8 },
      { path: 'delegationRules.maxChainLength', operation: 'modify', before: 3, after: 2 },
    ],
    riskAssessment: {
      impactLevel: 'medium',
      notes: 'Tightens thresholds while preserving the constitutional replay path.',
    },
  }, { persist: false });

  return {
    authorityContract,
    interoperabilityContract,
    conformanceRules,
    trustRelationships: relationships,
    governanceConfigs: configs,
    governanceDecisions: [],
    governanceProposals: [proposal],
    governanceTimeline: [
      buildPolityLifecycleEvent({
        eventId: 'boot-1',
        stage: 'birth',
        artifactId: 'sovereign-control-plane',
        createdAt: '2026-07-11T00:00:00.000Z',
        summary: 'Constitution loaded and the sovereign control plane came online.',
      }),
      buildPolityLifecycleEvent({
        eventId: 'growth-1',
        stage: 'growth',
        artifactId: 'rel-router-org',
        createdAt: '2026-07-11T00:05:00.000Z',
        summary: 'Router X joined as a governed citizen under the trust fabric.',
      }),
      buildPolityLifecycleEvent({
        eventId: 'governance-1',
        stage: 'governance',
        artifactId: 'proposal-trust-algebra-v1',
        createdAt: '2026-07-11T00:30:00.000Z',
        summary: 'A governance amendment was proposed to refine trust thresholds.',
      }),
      buildPolityLifecycleEvent({
        eventId: 'renewal-1',
        stage: 'renewal',
        artifactId: 'v1.1.0',
        createdAt: '2026-07-11T00:45:00.000Z',
        summary: 'The polity prepared a replay-backed renewal candidate.',
      }),
    ],
    governanceFeedback: [
      diagnoseConstitutionalDrift({
        diagnosisId: 'diagnosis-1',
        createdAt: '2026-07-11T00:20:00.000Z',
        trustDeltas: ['safety trust band dropped during replay'],
        governanceDeltas: ['safety threshold tightened'],
        routingDeltas: ['routing preference shifted toward higher trust'],
        delegationFailures: [],
        invariantViolations: [],
        replayRegressions: [],
        conformanceFailures: [],
      }),
    ],
    replaySessions: [replaySession],
    trustReceipts: relationships.flatMap((relationship) => [
      {
        receiptId: relationship.trustPacket.receiptId ?? relationship.trustResult.receipt.receiptId,
        subjectId: relationship.relationshipId,
        subjectKind: 'polity',
        parentId: null,
        hash: relationship.trustResult.receipt.hash,
        signature: relationship.trustResult.receipt.signature,
        replayIndex: relationship.trustResult.receipt.replayIndex,
        issuedAt: relationship.trustResult.receipt.issuedAt,
      } as ContinuityReceipt,
      ...relationship.receipts.continuityReceipts,
    ]),
    routeDecisions: [],
  };
}

function createGovernanceConfig(
  configVersion: string,
  domain: TrustDomain,
  tier: string,
  governanceLevel: 'basic' | 'enhanced' | 'full',
  minTrustScore: number,
  requiredBand: TrustBand,
  minEvidenceCount: number,
  minAuthorityChainLength: number,
): GovernanceConfigSnapshot {
  return {
    configVersion,
    domain,
    tier,
    thresholds: {
      minTrustScore,
      requiredBand,
      minEvidenceCount,
      minAuthorityChainLength,
    },
    algebraWeights: {
      confidence: 0.4,
      authority: 0.3,
      evidence: 0.3,
    },
    delegationRules: {
      maxChainLength: 3,
      minLinkTrustScore: 0.7,
    },
    trustPolicy: createTrustPolicy(domain, governanceLevel, configVersion, {
      minTrustScore,
      requiredBand,
      minEvidenceCount,
      minAuthorityChainLength,
    }),
  };
}

function createTrustPolicy(
  domain: TrustDomain,
  governanceLevel: 'basic' | 'enhanced' | 'full',
  policyVersion: string,
  overrides: ControlPlaneTrustPolicyOverrides = {},
): ControlPlaneTrustPolicy {
  const normalizedLevel = normalizeGovernanceLevel(governanceLevel);
  const baseTrustPolicy = trustPolicyForGovernanceLevel(normalizedLevel);
  return {
    ...baseTrustPolicy,
    policyId: `${domain}-${policyVersion}-${normalizedLevel}`,
    policyVersion,
    domain,
    governanceLevel: normalizedLevel,
    minTrustScore: overrides.minTrustScore ?? (normalizedLevel === 'full' ? 0.75 : normalizedLevel === 'enhanced' ? 0.55 : 0.2),
    requiredBand: overrides.requiredBand ?? (normalizedLevel === 'full' ? 'high' : normalizedLevel === 'enhanced' ? 'medium' : 'low'),
    preferHighTrustBand: overrides.preferHighTrustBand ?? normalizedLevel === 'full',
    minEvidenceCount: overrides.minEvidenceCount ?? (normalizedLevel === 'full' ? 3 : normalizedLevel === 'enhanced' ? 2 : 1),
    minAuthorityChainLength: overrides.minAuthorityChainLength ?? (normalizedLevel === 'full' ? 3 : normalizedLevel === 'enhanced' ? 2 : 1),
    confidenceWeight: 0.4,
    authorityWeight: 0.3,
    evidenceWeight: 0.3,
    replayRequired: true,
    conformanceRequired: true,
    standardsTraceabilityIds: [`stm-${domain}-${normalizedLevel}`],
  };
}

function normalizeGovernanceLevel(value: unknown): 'basic' | 'enhanced' | 'full' {
  return value === 'enhanced' || value === 'full' ? value : 'basic';
}

function createRelationshipRecord(input: {
  relationshipId: string;
  title: string;
  subjectId: string;
  objectId: string;
  relationshipKind: string;
  domain: TrustDomain;
  tier: string;
  governanceLevel: 'basic' | 'enhanced' | 'full';
  trustValues: { confidence: number; authorityLevel: number; evidenceStrength: number };
  evidenceIds: string[];
  authorityChain: string[];
  provenanceMethod: string;
  decisionType: TrustDecisionReport['decisionType'];
}): TrustRelationshipRecord {
  const trustView = calculateTrustView(
    input.trustValues.confidence,
    input.trustValues.authorityLevel,
    input.trustValues.evidenceStrength,
  );
  trustView.evidenceIds = [...input.evidenceIds];
  trustView.authority = {
    stewardId: input.authorityChain[0],
    delegationChainIds: [...input.authorityChain],
  };
  trustView.provenance = {
    originSystem: 'relationship-ledger',
    originActorId: input.authorityChain[0],
    method: input.provenanceMethod,
    createdAt: '2026-07-11T00:00:00.000Z',
    standardsTraceabilityIds: [`stm-${input.domain}-${input.tier}`],
  };

  const trustPolicy = createTrustPolicy(input.domain, input.governanceLevel, 'v1.0.0', {
    minTrustScore: input.governanceLevel === 'full' ? 0.75 : input.governanceLevel === 'enhanced' ? 0.55 : 0.2,
    requiredBand: input.governanceLevel === 'full' ? 'high' : input.governanceLevel === 'enhanced' ? 'medium' : 'low',
    minEvidenceCount: input.governanceLevel === 'full' ? 3 : input.governanceLevel === 'enhanced' ? 2 : 1,
    minAuthorityChainLength: input.governanceLevel === 'full' ? 3 : input.governanceLevel === 'enhanced' ? 2 : 1,
  });

  const trustInput: TrustEvaluationInput = {
    relationshipId: input.relationshipId,
    subjectId: input.subjectId,
    objectId: input.objectId,
    confidence: input.trustValues.confidence,
    authorityLevel: input.trustValues.authorityLevel,
    evidenceStrength: input.trustValues.evidenceStrength,
    evidenceIds: [...input.evidenceIds],
    authorityChain: [...input.authorityChain],
    provenance: {
      originSystem: 'relationship-ledger',
      originActorId: input.authorityChain[0],
      method: input.provenanceMethod,
      createdAt: '2026-07-11T00:00:00.000Z',
      standardsTraceabilityIds: [`stm-${input.domain}-${input.tier}`],
    },
  };

  const trustResult = evaluateTrustPolicy(trustInput, trustPolicy);
  const trustProvenance = {
    ...trustResult.assertion.provenance,
    createdAt: trustResult.assertion.provenance.createdAt ?? '2026-07-11T00:00:00.000Z',
  };
  const trustPacket = buildRelationshipTrustPacket({
    relationshipId: input.relationshipId,
    revision: 2,
    subjectId: input.subjectId,
    objectId: input.objectId,
    relationshipKind: input.relationshipKind,
    governanceLevel: input.governanceLevel,
    authorityChain: [...input.authorityChain],
    trust: trustResult.assertion
      ? {
          score: trustResult.score,
          band: trustResult.band,
          evidenceIds: [...trustResult.evidenceIds],
          authority: trustResult.assertion.provenance.originActorId
            ? {
                stewardId: trustResult.assertion.provenance.originActorId,
                delegationChainIds: [...input.authorityChain],
              }
            : undefined,
          provenance: trustProvenance,
        }
      : trustView,
    ledgerEntryId: `ledger-${input.relationshipId}`,
    receiptId: trustResult.receipt.receiptId,
    capturedAt: trustResult.receipt.issuedAt,
  });

  const candidateScores: Array<{
    id: string;
    baseScore: number;
    trustScore: number;
    governanceStatus: TrustDecisionResult;
    finalScore: number;
  }> = [
    {
      id: `${input.objectId}-preferred`,
      baseScore: round(input.trustValues.confidence),
      trustScore: round(trustResult.score),
      governanceStatus: trustResult.result,
      finalScore: round((trustResult.score * 0.6) + (input.trustValues.confidence * 0.4)),
    },
    {
      id: `${input.objectId}-fallback`,
      baseScore: round(Math.max(0.3, input.trustValues.confidence - 0.12)),
      trustScore: round(Math.max(0.2, trustResult.score - 0.15)),
      governanceStatus: trustResult.result === 'blocked' ? 'blocked' : 'warning',
      finalScore: round(Math.max(0.1, (trustResult.score * 0.5) + (input.trustValues.confidence * 0.35) - 0.08)),
    },
  ];

  const decisionReport = buildTrustDecisionReport({
    decisionId: `decision-${input.relationshipId}`,
    decisionType: input.decisionType,
    artifactId: input.relationshipId,
    relationshipId: input.relationshipId,
    trustResult,
    candidates: candidateScores,
    ledgerEntryId: `ledger-${input.relationshipId}`,
    previousHash: null,
    signature: trustResult.receipt.signature,
    replayIndex: 1,
    narrativeSummary: `Trust decision for ${input.title} remained constitutional under ${trustPolicy.governanceLevel} governance.`,
  });

  const revisions: ConstitutionalArtifactRevision[] = [
    {
      artifactId: `${input.relationshipId}-rev-1`,
      artifactKind: 'clause',
      version: '1.0.0',
      parentId: null,
      previousHash: null,
      hash: hashJson({ relationshipId: input.relationshipId, revision: 1, trustScore: trustResult.score }),
      signature: hashJson({ relationshipId: input.relationshipId, revision: 1, signature: true }),
      timestamp: '2026-07-11T00:00:00.000Z',
      replayContext: {
        mode: 'historical',
        scope: 'relationship',
        configVersionUsed: trustPolicy.policyVersion,
        timeRange: {
          start: '2026-07-11T00:00:00.000Z',
          end: '2026-07-11T00:30:00.000Z',
        },
      },
      content: {
        relationshipId: input.relationshipId,
        trustScore: round(trustResult.score - 0.03),
        trustBand: trustBandFromScore(round(trustResult.score - 0.03)),
      },
    },
    {
      artifactId: `${input.relationshipId}-rev-2`,
      artifactKind: 'amendment',
      version: '1.0.1',
      parentId: `${input.relationshipId}-rev-1`,
      previousHash: hashJson({ relationshipId: input.relationshipId, revision: 1, trustScore: trustResult.score }),
      hash: hashJson({ relationshipId: input.relationshipId, revision: 2, trustScore: trustResult.score }),
      signature: hashJson({ relationshipId: input.relationshipId, revision: 2, signature: true }),
      timestamp: '2026-07-11T00:30:00.000Z',
      replayContext: {
        mode: 'counterfactual',
        scope: 'relationship',
        configVersionUsed: trustPolicy.policyVersion,
        timeRange: {
          start: '2026-07-11T00:00:00.000Z',
          end: '2026-07-11T01:00:00.000Z',
        },
      },
      content: {
        relationshipId: input.relationshipId,
        trustScore: trustResult.score,
        trustBand: trustResult.band,
      },
    },
  ];

  const continuityReceipts = revisions.map((revision, index) =>
    createContinuityReceipt({
      subjectId: revision.artifactId,
      subjectKind: 'amendment',
      parentId: revision.parentId,
      payload: revision,
      replayIndex: index,
      issuedAt: revision.timestamp,
    }),
  );

  return {
    relationshipId: input.relationshipId,
    title: input.title,
    domain: input.domain,
    tier: input.tier,
    relationshipKind: input.relationshipKind,
    subjectId: input.subjectId,
    objectId: input.objectId,
    trustPacket,
    trustPolicy,
    trustResult,
    decisionReport,
    revisions,
    receipts: {
      trustReceipt: trustResult.receipt,
      continuityReceipts,
    },
    debugTemplate: {
      decisionType: input.decisionType,
      candidates: candidateScores,
      narrativeSummary: decisionReport.plainLanguageSummary,
      ledgerEntryId: `ledger-${input.relationshipId}`,
      previousHash: null,
      signature: trustResult.receipt.signature,
      replayIndex: 1,
    },
  };
}

function buildPlaneConformanceReport(): ConstitutionalConformanceReport {
  const checks: PlaneConformanceCheck[] = [
    {
      plane: 'governance',
      status: 'conformant',
      reasons: [],
      evidenceIds: ['ev-governance-config', 'ev-governance-replay'],
      replayable: true,
      lineagePreserved: true,
      trustAligned: true,
    },
    {
      plane: 'knowledge',
      status: 'conformant',
      reasons: [],
      evidenceIds: ['ev-knowledge-traceability', 'ev-ontology'],
      replayable: true,
      lineagePreserved: true,
      trustAligned: true,
    },
    {
      plane: 'execution',
      status: 'conformant',
      reasons: [],
      evidenceIds: ['ev-execution-router', 'ev-execution-cep'],
      replayable: true,
      lineagePreserved: true,
      trustAligned: true,
    },
    {
      plane: 'control',
      status: 'conformant',
      reasons: [],
      evidenceIds: ['ev-control-plane', 'ev-control-replay'],
      replayable: true,
      lineagePreserved: true,
      trustAligned: true,
    },
  ];

  return evaluatePlaneConformance(checks, conformanceRules);
}

function hashJson(value: unknown): string {
  return crypto.createHash('sha256').update(JSON.stringify(sortValue(value))).digest('hex');
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

function round(value: number): number {
  return Number(value.toFixed(4));
}

function trustBandFromScore(score: number): TrustBand {
  if (score < 0.33) return 'low';
  if (score < 0.66) return 'medium';
  return 'high';
}

function setDeepValue(target: Record<string, unknown>, path: string, value: unknown): void {
  const parts = path.split('.').filter(Boolean);
  if (parts.length === 0) {
    return;
  }
  let cursor: Record<string, unknown> = target;
  while (parts.length > 1) {
    const key = parts.shift()!;
    const current = cursor[key];
    if (!current || typeof current !== 'object' || Array.isArray(current)) {
      cursor[key] = {};
    }
    cursor = cursor[key] as Record<string, unknown>;
  }
  cursor[parts[0]] = value;
}
