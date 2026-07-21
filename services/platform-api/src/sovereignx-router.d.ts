declare module '@aaes-os/sovereignx-router' {
  export type TrustBand = 'low' | 'medium' | 'high';

  export interface TrustAuthority {
    stewardId?: string;
    consentArtifactIds?: string[];
    delegationChainIds?: string[];
  }

  export interface TrustProvenance {
    originSystem: string;
    originActorId?: string;
    method: string;
    createdAt?: string;
    standardsTraceabilityIds?: string[];
  }

  export interface RelationshipTrustView {
    score: number;
    band: TrustBand;
    evidenceIds: string[];
    authority?: TrustAuthority;
    provenance?: TrustProvenance;
  }

  export type GovernanceTrustLevel = 'basic' | 'enhanced' | 'full';

  export interface GovernanceTrustPolicy {
    governanceLevel: GovernanceTrustLevel;
    minTrustScore: number;
    minTrustBand?: TrustBand;
    preferHighTrustBand?: boolean;
  }

  export interface RelationshipLedgerTrustPacket {
    relationshipId: string;
    revision: number;
    subjectId?: string;
    objectId?: string;
    relationshipKind?: string;
    ledgerEntryId?: string;
    receiptId?: string;
    capturedAt?: string;
    governanceLevel: GovernanceTrustLevel;
    authorityChain: string[];
    trust: RelationshipTrustView;
    signature?: {
      algorithm: 'HMAC-SHA256' | 'Ed25519';
      value: string;
      signer?: string;
      signedAt?: string;
    };
  }

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
    governanceLevel: GovernanceTrustLevel;
    minTrustScore: number;
    requiredBand: TrustBand;
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
        type: 'routing' | 'promotion' | 'delegation' | 'governance';
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

  export type SovereignRouterXPricingSegment =
    | 'Individual'
    | 'Professional'
    | 'Team'
    | 'Enterprise'
    | 'Public Sector';

  export type SovereignRouterXPricingStrategy =
    | 'Subscription-led'
    | 'Usage-led'
    | 'Assurance-led'
    | 'Enterprise bundle';

  export interface SovereignRouterXPricingInput {
    segment: SovereignRouterXPricingSegment;
    monthlyCustomers: number;
    routedRequestsPerCustomer: number;
    governanceReviewsPerCustomer: number;
    knowledgeUpdatesPerCustomer: number;
    serviceHoursPerCustomer: number;
    compliancePressure: number;
    workloadVolatility: number;
    supportComplexity: number;
    privateDeployment: boolean;
    assuranceRequired: boolean;
    governanceLevel?: GovernanceTrustLevel;
    trust?: RelationshipTrustView;
  }

  export interface SovereignRouterXPricingScenario {
    strategy: SovereignRouterXPricingStrategy;
    packaging: string;
    valueFocus: string;
    marginDriver: string;
    targetMarginBand: string;
    score: number;
    estimatedRevenueUsd: number;
    estimatedCostUsd: number;
    estimatedGrossMarginUsd: number;
    estimatedGrossMarginPct: number;
    trustPolicy: GovernanceTrustPolicy;
  }

  export interface SovereignRouterXPricingLedgerEntry {
    requestId: string;
    recordedAt: string;
    segment: SovereignRouterXPricingSegment;
    strategy: SovereignRouterXPricingStrategy;
    routedRequests: number;
    monthlyCustomers: number;
    estimatedRevenueUsd: number;
    estimatedCostUsd: number;
    estimatedGrossMarginUsd: number;
    estimatedGrossMarginPct: number;
    selectedModel: { model: string; reason: string; overrideApplied: boolean; trust?: RelationshipTrustView };
    backend: string;
    routeReason: string;
  }

  export interface SovereignRouterXPricingRequestPacket {
    objective: string;
    current_state?: string;
    done: string[];
    next_action: string;
    files: string[];
    verification: string;
    blockers: string[];
    governanceLevel?: GovernanceTrustLevel;
    trust?: RelationshipTrustView;
  }

  export interface SovereignRouterXPricingEvaluation {
    input: SovereignRouterXPricingInput;
    requestPacket: SovereignRouterXPricingRequestPacket;
    strategyScenarios: SovereignRouterXPricingScenario[];
    recommendedScenario: SovereignRouterXPricingScenario;
    routing: {
      routeEvaluation: unknown;
      backend: string;
      modelDecision: { model: string; reason: string; overrideApplied: boolean; trust?: RelationshipTrustView };
      routingHint: unknown;
      trust?: RelationshipTrustView;
      trustPolicy: GovernanceTrustPolicy;
    };
    economics: {
      monthlyRevenueUsd: number;
      monthlyDirectCostUsd: number;
      grossMarginUsd: number;
      grossMarginPct: number;
      routedRequests: number;
      requestRevenueUsd: number;
      requestCostUsd: number;
      requestGrossMarginUsd: number;
      requestGrossMarginPct: number;
    };
    ledgerEntry: SovereignRouterXPricingLedgerEntry;
  }

  export interface RouteDecisionArtifactSignature {
    algorithm: 'HMAC-SHA256';
    signer: string;
    signedAt: string;
    value: string;
  }

  export interface RouteGovernanceDecision {
    result: 'allowed' | 'warning' | 'blocked';
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

  export interface CanonicalRouteDecisionArtifact {
    version: '1.0';
    artifactId: string;
    requestId: string;
    orgId: string;
    customerId?: string;
    relationshipId: string;
    createdAt: string;
    trustPacket: RelationshipLedgerTrustPacket;
    routeEvaluation: unknown;
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
    trustPolicy: GovernanceTrustPolicy & {
      requiredBand?: TrustBand;
      minEvidenceCount?: number;
      minAuthorityChainLength?: number;
    };
    routeEvaluation: unknown;
    provenance: RouteDecisionProvenance;
    decidedBy?: string;
    decidedAt?: string;
    configVersion?: string;
    replay?: RouteDecisionReplayContext;
    signingSecret?: string;
    signer?: string;
  }

  export function trustPolicyForGovernanceLevel(
    governanceLevel: GovernanceTrustLevel | string | undefined | null,
  ): GovernanceTrustPolicy;

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
  }): RelationshipLedgerTrustPacket;

  export function signRelationshipTrustPacket(
    packet: RelationshipLedgerTrustPacket,
    secret: string,
    signer?: string,
    signedAt?: string,
  ): {
    algorithm: 'HMAC-SHA256';
    signer: string;
    signedAt: string;
    value: string;
  };

  export function verifyRelationshipTrustPacket(
    packet: RelationshipLedgerTrustPacket,
    signature: {
      algorithm: 'HMAC-SHA256';
      signer: string;
      signedAt: string;
      value: string;
    } | undefined,
    secret: string,
  ): boolean;

  export function buildRouteDecisionArtifact(
    input: BuildRouteDecisionArtifactInput,
  ): CanonicalRouteDecisionArtifact;

  export function verifyRouteDecisionArtifact(
    artifact: CanonicalRouteDecisionArtifact,
    signingSecret: string,
  ): boolean;

  export function calculateTrustView(
    confidence: number,
    authorityLevel: number,
    evidenceStrength: number,
    weights?: {
      confidenceWeight: number;
      authorityWeight: number;
      evidenceWeight: number;
    },
  ): RelationshipTrustView;

  export function evaluateSovereignRouterXPricing(
    input: Partial<SovereignRouterXPricingInput> & Pick<SovereignRouterXPricingInput, 'segment'>,
    options?: { requestId?: string },
  ): SovereignRouterXPricingEvaluation;

  export function normalizeSovereignRouterXPricingInput(
    input: Partial<SovereignRouterXPricingInput> & Pick<SovereignRouterXPricingInput, 'segment'>,
  ): SovereignRouterXPricingInput;

  export function createPricingLedgerEntry(
    evaluation: SovereignRouterXPricingEvaluation,
  ): SovereignRouterXPricingLedgerEntry;

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

  export function validateConstitutionalLineage(
    revisions: ConstitutionalArtifactRevision[],
  ): ContinuityValidationResult;

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
  }): GovernanceConfigDiff;

  export function evaluateReplayValidation(
    contract: ReplayValidationContract,
    report: TrustReplayReport,
  ): ReplayValidationResult;

  export function evaluatePlaneConformance(
    checks: PlaneConformanceCheck[],
    rules: PlaneConformanceRule[],
  ): ConstitutionalConformanceReport;

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
  }): ConstitutionalDiagnosisReport;

  export function evaluateGovernanceKernelV3(
    input: GovernanceKernelV3Input,
  ): GovernanceKernelV3Decision;

  export function buildPolityLifecycleEvent(input: {
    eventId: string;
    stage: PolityLifecycleStage;
    artifactId: string;
    createdAt: string;
    summary: string;
  }): PolityLifecycleEvent;

  export function buildCSAAuthorityContract(): CSAAuthorityContract;
}
