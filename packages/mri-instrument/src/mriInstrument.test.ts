import { describe, expect, it } from 'vitest';

import {
  computeConfidence,
  computeContinuityComponents,
  computeDeltaState,
  continuityScore,
  generateBeforeAfterReport,
  governanceScore,
  memoryScore,
  recommendInterventions,
  runMRIComparison,
  type OrgMeasurement,
} from './index.js';

const before: OrgMeasurement = {
  orgId: 'aaes-os-pilot',
  label: 'AAES OS pilot before',
  phase: 'before',
  measuredAt: '2026-06-18T10:00:00.000Z',
  continuityInputs: {
    singlePointsOfFailure: 4,
    criticalRoles: 10,
    documentedKnowledge: 5,
    totalRequiredKnowledge: 10,
    clearGovernanceElements: 6,
    totalGovernanceElements: 10,
    medianDecisionTime: 4,
    expectedDecisionTime: 10,
    coordinationLoad: 7,
    coordinationCapacity: 10,
  },
  governanceInputs: {
    authorityClarity: 60,
    escalationClarity: 50,
    roleDefinitionQuality: 65,
    decisionTransparency: 55,
  },
  memoryInputs: {
    documentationCoverage: 50,
    artifactAccessibility: 65,
    successionReadiness: 40,
  },
  confidenceInputs: {
    observationCompleteness: 0.8,
    dataQuality: 0.7,
    sourceReliability: 0.9,
    temporalFreshness: 0.6,
  },
};

const after: OrgMeasurement = {
  ...before,
  label: 'AAES OS pilot after',
  phase: 'after',
  measuredAt: '2026-06-18T11:00:00.000Z',
  continuityInputs: {
    singlePointsOfFailure: 1,
    criticalRoles: 10,
    documentedKnowledge: 8,
    totalRequiredKnowledge: 10,
    clearGovernanceElements: 8,
    totalGovernanceElements: 10,
    medianDecisionTime: 2,
    expectedDecisionTime: 10,
    coordinationLoad: 4,
    coordinationCapacity: 10,
  },
  governanceInputs: {
    authorityClarity: 80,
    escalationClarity: 78,
    roleDefinitionQuality: 82,
    decisionTransparency: 76,
  },
  memoryInputs: {
    documentationCoverage: 80,
    artifactAccessibility: 78,
    successionReadiness: 72,
  },
  confidenceInputs: {
    observationCompleteness: 0.9,
    dataQuality: 0.85,
    sourceReliability: 0.9,
    temporalFreshness: 0.8,
  },
};

describe('MRI v0.1 instrument', () => {
  it('computes continuity components and clamps invalid ratios', () => {
    expect(computeContinuityComponents(before.continuityInputs)).toEqual({
      R: 60,
      K: 50,
      G: 60,
      D: 60,
      X: 30,
    });

    expect(
      computeContinuityComponents({
        ...before.continuityInputs,
        criticalRoles: 0,
        totalRequiredKnowledge: 0,
        totalGovernanceElements: 0,
        expectedDecisionTime: 0,
        coordinationCapacity: 0,
      }),
    ).toEqual({
      R: 0,
      K: 0,
      G: 0,
      D: 0,
      X: 0,
    });
  });

  it('computes canonical continuity, governance, memory, and confidence scores', () => {
    expect(continuityScore({ R: 60, K: 50, G: 60, D: 60, X: 30 })).toBe(53);
    expect(governanceScore(before.governanceInputs)).toBe(57.75);
    expect(memoryScore(before.memoryInputs)).toBe(52.75);
    expect(computeConfidence(before.confidenceInputs)).toBe(0.75);
  });

  it('computes institutional state transition', () => {
    expect(
      computeDeltaState(
        { R: 60, K: 50, G: 60, D: 60, X: 30 },
        { R: 90, K: 80, G: 80, D: 80, X: 60 },
      ),
    ).toEqual({ R: 30, K: 30, G: 20, D: 20, X: 30 });
  });

  it('ranks interventions with confidence weighting', () => {
    const lowConfidence = runMRIComparison(before, after).before.interventions;
    const direct = recommendInterventions(runMRIComparison(before, after).before.risks, 0.75);

    expect(direct[0]?.type).toBe('documentation_sprint');
    expect(lowConfidence[0]?.score).toBe(direct[0]?.score);
    expect(direct.every((intervention) => intervention.score > 0)).toBe(true);
  });

  it('generates a before/after report with state delta and confidence', () => {
    const comparison = runMRIComparison(before, after);
    const report = generateBeforeAfterReport(comparison);

    expect(comparison.deltaState).toEqual({ R: 30, K: 30, G: 20, D: 20, X: 30 });
    expect(comparison.after.scores.continuity).toBeGreaterThan(comparison.before.scores.continuity);
    expect(report.summary).toContain('Continuity increased by');
    expect(report.largestStateTransitions[0]).toEqual({ key: 'R', delta: 30 });
    expect(report.beforeConfidence).toBe(0.75);
    expect(report.afterConfidence).toBe(0.865);
  });
});
