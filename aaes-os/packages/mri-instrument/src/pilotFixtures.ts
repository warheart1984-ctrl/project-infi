import type { BenchmarkSnapshot, OrgMeasurement } from './index.js';

/** Pilot before measurement (aligned with mriInstrument.test.ts). */
export const PILOT_BEFORE: OrgMeasurement = {
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

/** Pilot after measurement. */
export const PILOT_AFTER: OrgMeasurement = {
  ...PILOT_BEFORE,
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
    sourceReliability: 0.92,
    temporalFreshness: 0.88,
  },
};

/** Seeded benchmark tiers for pilot / ops-console (0–100 scale). */
export const PILOT_BENCHMARKS: BenchmarkSnapshot = {
  industryAverage: {
    continuity: 61,
    governance: 59,
    memory: 64,
    coordination: 57,
    confidence: 70,
  },
  topQuartile: {
    continuity: 78,
    governance: 74,
    memory: 82,
    coordination: 71,
    confidence: 85,
  },
  previousMeasurement: {
    continuity: 64,
    governance: 72,
    memory: 64,
    coordination: 65,
    confidence: 75,
  },
};
