import { describe, expect, it } from 'vitest';

import {
  buildCSAAuthorityContract,
  buildPolityLifecycleEvent,
  diagnoseConstitutionalDrift,
  evaluateGovernanceKernelV3,
  evaluatePlaneConformance,
  evaluateReplayValidation,
  synthesizeGovernanceConfigDiff,
  validateConstitutionalLineage,
  type ConstitutionalArtifactRevision,
  type GovernanceChangeProposal,
  type ReplayValidationContract,
  type TrustReplayReport,
} from './continuity.js';

const lineage: ConstitutionalArtifactRevision[] = [
  {
    artifactId: 'invariant-1',
    artifactKind: 'invariant',
    version: '1.0.0',
    parentId: null,
    previousHash: null,
    hash: 'hash-root',
    signature: 'sig-root',
    timestamp: '2026-07-11T00:00:00.000Z',
    replayContext: {
      mode: 'historical',
      scope: 'global',
      configVersionUsed: 'v1.0.0',
      timeRange: {
        start: '2026-07-11T00:00:00.000Z',
        end: '2026-07-11T00:00:00.000Z',
      },
    },
    content: { description: 'root invariant' },
  },
  {
    artifactId: 'amendment-1',
    artifactKind: 'amendment',
    version: '1.0.1',
    parentId: 'invariant-1',
    previousHash: 'hash-root',
    hash: 'hash-child',
    signature: 'sig-child',
    timestamp: '2026-07-11T01:00:00.000Z',
    replayContext: {
      mode: 'counterfactual',
      scope: 'global',
      configVersionUsed: 'v1.0.1',
      timeRange: {
        start: '2026-07-11T00:00:00.000Z',
        end: '2026-07-11T01:00:00.000Z',
      },
    },
    content: { description: 'amendment' },
  },
];

const replayReport: TrustReplayReport = {
  replayId: 'replay-1',
  createdAt: '2026-07-11T02:00:00.000Z',
  mode: 'counterfactual',
  scope: 'global',
  configVersionUsed: 'v1.0.1',
  timeRange: {
    start: '2026-07-11T00:00:00.000Z',
    end: '2026-07-11T01:00:00.000Z',
  },
  summary: {
    decisionsChanged: 1,
    trustBandsChanged: 0,
    governanceOutcomesChanged: 0,
  },
  narrativeSummary: 'Replay shows the amendment is stable.',
  results: {
    decisions: [
      {
        decisionId: 'decision-1',
        type: 'routing',
        originalOutcome: 'allowed',
        replayedOutcome: 'allowed',
        changed: false,
        affectedComponents: ['routing'],
      },
    ],
    trustDeltas: [],
    governanceDeltas: [],
  },
  hash: 'replay-hash',
  signature: 'replay-sig',
};

describe('Continuity Engine', () => {
  it('validates constitutional lineage with parent and hash chaining', () => {
    const result = validateConstitutionalLineage(lineage);
    expect(result.valid).toBe(true);
    expect(result.chain).toHaveLength(2);
  });

  it('rejects lineage that breaks the parent chain', () => {
    const broken = lineage.map((entry, index) =>
      index === 1 ? { ...entry, parentId: 'wrong-parent' } : entry,
    );

    const result = validateConstitutionalLineage(broken);
    expect(result.valid).toBe(false);
    expect(result.reasons.some((reason) => reason.includes('wrong-parent'))).toBe(true);
  });

  it('synthesizes structured governance diffs', () => {
    const diff = synthesizeGovernanceConfigDiff({
      diffId: 'diff-1',
      createdAt: '2026-07-11T02:00:00.000Z',
      currentConfigVersion: 'v1.0.0',
      targetConfigVersion: 'v1.0.1',
      domain: 'global',
      tier: 'core',
      currentConfig: {
        trust: { minScore: 0.7, requiredBand: 'high' },
      },
      proposedConfig: {
        trust: { minScore: 0.8, requiredBand: 'high' },
      },
      replayReportIds: ['replay-1'],
      trustReportIds: ['trust-1'],
    });

    expect(diff.changes.some((change) => change.path === 'trust.minScore')).toBe(true);
  });

  it('evaluates replay validation against contract criteria', () => {
    const contract: ReplayValidationContract = {
      configVersionUsed: 'v1.0.1',
      scope: 'global',
      requiredDomains: ['global'],
      requiredRelationships: ['relationship-1'],
      requiredTiers: ['core'],
      requiredRoutingDecisions: ['decision-1'],
      requiredTrustArtifacts: ['trust-1'],
      requireHistoricalReplay: false,
      requireCounterfactualReplay: true,
      maxAllowedDecisionsChanged: 2,
      maxAllowedTrustBandDrops: 1,
      maxAllowedGovernanceRegressions: 1,
    };

    const result = evaluateReplayValidation(contract, replayReport);
    expect(result.passed).toBe(true);
    expect(result.metrics.decisionsChanged).toBe(1);
  });

  it('produces a constitutional governance decision from continuity inputs', () => {
    const conformance = evaluatePlaneConformance(
      [
        {
          plane: 'governance',
          status: 'conformant',
          reasons: [],
          evidenceIds: ['evidence-1'],
          replayable: true,
          lineagePreserved: true,
          trustAligned: true,
        },
        {
          plane: 'knowledge',
          status: 'conformant',
          reasons: [],
          evidenceIds: ['evidence-2'],
          replayable: true,
          lineagePreserved: true,
          trustAligned: true,
        },
        {
          plane: 'execution',
          status: 'conformant',
          reasons: [],
          evidenceIds: ['evidence-3'],
          replayable: true,
          lineagePreserved: true,
          trustAligned: true,
        },
      ],
      [
        { id: 'replay-required', description: 'replay must be preserved', required: true },
        { id: 'lineage-required', description: 'lineage must be preserved', required: true },
        { id: 'trust-required', description: 'trust must be aligned', required: true },
      ],
    );

    const decision = evaluateGovernanceKernelV3({
      actionType: 'routing',
      domain: 'global',
      tier: 'core',
      trustScore: 0.81,
      trustBand: 'high',
      evidenceIds: ['evidence-1'],
      authorityChain: ['steward-1'],
      policyResult: 'allowed',
      policyFactor: 1,
      clauseViolations: [],
      conformance,
      replay: evaluateReplayValidation(
        {
          configVersionUsed: 'v1.0.1',
          scope: 'global',
          requiredDomains: ['global'],
          requiredRelationships: [],
          requiredTiers: [],
          requiredRoutingDecisions: [],
          requiredTrustArtifacts: [],
          requireHistoricalReplay: false,
          requireCounterfactualReplay: true,
        },
        replayReport,
      ),
    });

    expect(decision.result).toBe('allowed');
    expect(decision.governanceFactor).toBe(1);
  });

  it('emits CSA authority and lifecycle artifacts', () => {
    expect(buildCSAAuthorityContract().constraints.replayValidationRequired).toBe(true);
    expect(
      buildPolityLifecycleEvent({
        eventId: 'event-1',
        stage: 'birth',
        artifactId: 'constitutional-oath',
        createdAt: '2026-07-11T00:00:00.000Z',
        summary: 'The polity came online.',
      }).stage,
    ).toBe('birth');

    const diagnosis = diagnoseConstitutionalDrift({
      diagnosisId: 'diag-1',
      createdAt: '2026-07-11T03:00:00.000Z',
      trustDeltas: ['trust band dropped'],
      governanceDeltas: ['threshold mismatch'],
      routingDeltas: ['routing weight drift'],
      delegationFailures: ['delegation chain too long'],
      invariantViolations: ['lineage broken'],
      replayRegressions: ['counterfactual regression'],
      conformanceFailures: ['execution plane partial'],
    });

    expect(diagnosis.recommendedAmendments).toContain('review trust algebra thresholds and weights');
  });

  it('accepts the user-facing governance change proposal shape', () => {
    const proposal: GovernanceChangeProposal = {
      proposalId: 'proposal-1',
      createdAt: '2026-07-11T03:00:00.000Z',
      createdByStewardId: 'steward-1',
      motivation: {
        summary: 'Tune trust thresholds after repeated anomalies.',
        linkedDecisionIds: ['decision-1'],
        linkedFeedbackIds: ['feedback-1'],
        linkedReplayReportIds: ['replay-1'],
        externalPolicyReferences: ['policy-1'],
      },
      currentConfigVersion: 'v1.0.0',
      targetConfigVersion: 'v1.0.1',
      affectedDomains: ['global'],
      affectedTiers: ['core'],
      affectedDelegationChains: ['chain-1'],
      affectedTrustAlgebraComponents: ['weights'],
      affectedConformanceRules: ['replay-required'],
      proposedChanges: [
        {
          path: 'trust.minScore',
          operation: 'modify',
          before: 0.7,
          after: 0.8,
        },
      ],
      riskAssessment: {
        impactLevel: 'medium',
        notes: 'Conservative threshold increase.',
      },
    };

    expect(proposal.proposedChanges[0].path).toBe('trust.minScore');
  });
});
