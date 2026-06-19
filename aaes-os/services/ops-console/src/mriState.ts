import {
  buildMRIOutputV2,
  PILOT_AFTER,
  PILOT_BEFORE,
  PILOT_BENCHMARKS,
  runMRIComparison,
  type BeforeAfterReport,
  type Intervention,
  type MRIComparison,
  type MRIOutputV2,
  type Risk,
} from '@aaes-os/mri-instrument';

export interface MRIAssessment {
  comparison: MRIComparison;
  report: BeforeAfterReport;
  risks: Risk[];
  interventions: Intervention[];
}

export function getSeededBenchmarkSnapshot() {
  return PILOT_BENCHMARKS;
}

const confidenceInputs = {
  observationCompleteness: 0.85,
  dataQuality: 0.8,
  sourceReliability: 0.78,
  temporalFreshness: 0.82,
  crossEvidenceConsistency: 0.76,
};

export function getSeededMriAssessment(): MRIAssessment {
  const result = runMRIComparison(PILOT_BEFORE, PILOT_AFTER);
  return {
    comparison: result,
    report: {
      orgId: result.orgId,
      beforeContinuity: result.before.scores.continuity,
      afterContinuity: result.after.scores.continuity,
      continuityDelta: result.after.scores.continuity - result.before.scores.continuity,
      beforeConfidence: result.before.scores.confidence,
      afterConfidence: result.after.scores.confidence,
      largestStateTransitions: Object.entries(result.deltaState)
        .map(([key, delta]) => ({ key: key as keyof typeof result.deltaState, delta }))
        .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)),
      summary: `Continuity increased by ${result.after.scores.continuity - result.before.scores.continuity} points with confidence ${result.after.scores.confidence}.`,
    },
    risks: result.after.risks,
    interventions: result.after.interventions,
  };
}

export function getSeededMriAssessmentV2(): MRIOutputV2 {
  const result = runMRIComparison(PILOT_BEFORE, PILOT_AFTER);
  return buildMRIOutputV2(result, getSeededBenchmarkSnapshot(), confidenceInputs);
}
