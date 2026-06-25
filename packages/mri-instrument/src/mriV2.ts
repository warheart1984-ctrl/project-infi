import type { BenchmarkSnapshot, ConfidenceInputs, MRIComparison } from './index.js';
import {
  computeBenchmarkDeltas,
  computePublicDeltaState,
  publicScoresFromComparison,
  scoresToBenchmarkPoints,
  summarizeBenchmarksDetailed,
} from './benchmark.js';
import { computeConfidenceTensor, confidenceTensorScalar } from './confidenceTensor.js';
import {
  buildTrajectoryBreakdown,
  classifyTrajectorySignatures,
  computeTrajectoryVector,
  projectPublicState,
  type TrajectoryVector,
} from './trajectory.js';

export type MRIOutputV2 = {
  timestamp: string;
  orgId: string;
  label: string;
  state_vector: {
    continuity: number;
    governance: number;
    memory: number;
    coordination: number;
    confidence: number;
  };
  delta_state: {
    continuity: number;
    governance: number;
    memory: number;
    coordination: number;
    confidence: number;
  };
  trajectory_vector: TrajectoryVector & {
    confidence_weighted_magnitude: number;
  };
  benchmarks: BenchmarkSnapshot & {
    summary: string;
    deltas: ReturnType<typeof computeBenchmarkDeltas>;
    bar_markers: ReturnType<typeof scoresToBenchmarkPoints>;
  };
  trajectory_signatures: ReturnType<typeof classifyTrajectorySignatures>;
  trajectory_breakdown: ReturnType<typeof buildTrajectoryBreakdown>;
  projection: ReturnType<typeof projectPublicState>;
  risks: MRIComparison['before']['risks'];
  interventions: MRIComparison['before']['interventions'];
  evidence: {
    beforeConfidence: number;
    afterConfidence: number;
    meanConfidence: number;
    confidenceTensor: ReturnType<typeof computeConfidenceTensor>;
  };
  before_after: {
    before: ReturnType<typeof publicScoresFromComparison>['before'];
    after: ReturnType<typeof publicScoresFromComparison>['after'];
  };
  invariant_fitness?: InvariantFitnessResult;
};

export type InvariantFitnessResult = {
  verdict: 'promote' | 'retain' | 'revert';
  improvedDimensions: string[];
  meanConfidence: number;
  fitnessScore: number;
};

type FitnessDeltaInput = {
  continuity: number;
  governance: number;
  memory: number;
  coordination: number;
  confidence?: number;
};

const PROMOTE_THRESHOLD = 0.02;
const REVERT_THRESHOLD = -0.02;
const MIN_CONFIDENCE_FOR_PROMOTE = 0.55;

/** Evaluate constitutional hardening from score-scale deltas, not normalized deltas. */
export function evaluateInvariantFitness(
  deltaScores: FitnessDeltaInput,
  meanConfidence: number,
): InvariantFitnessResult {
  const dims = ['continuity', 'governance', 'memory', 'coordination'] as const;
  const improvedDimensions = dims.filter((dimension) => deltaScores[dimension] > 0);
  const fitnessScore =
    dims.reduce((sum, dimension) => sum + deltaScores[dimension], 0) /
    (dims.length * 100);

  let verdict: InvariantFitnessResult['verdict'] = 'retain';
  if (fitnessScore >= PROMOTE_THRESHOLD && meanConfidence >= MIN_CONFIDENCE_FOR_PROMOTE) {
    verdict = 'promote';
  } else if (fitnessScore <= REVERT_THRESHOLD) {
    verdict = 'revert';
  }

  return { verdict, improvedDimensions, meanConfidence, fitnessScore };
}

function scoreScaleDeltas(
  before: ReturnType<typeof publicScoresFromComparison>['before'],
  after: ReturnType<typeof publicScoresFromComparison>['after'],
): FitnessDeltaInput {
  return {
    continuity: after.continuity - before.continuity,
    governance: after.governance - before.governance,
    memory: after.memory - before.memory,
    coordination: after.coordination - before.coordination,
    confidence: after.confidence - before.confidence,
  };
}

export function buildMRIOutputV2(
  comparison: MRIComparison,
  benchmarks: BenchmarkSnapshot,
  confidenceInputs?: ConfidenceInputs & { crossEvidenceConsistency?: number },
): MRIOutputV2 {
  const { before: beforePublic, after: afterPublic } = publicScoresFromComparison(comparison);
  const deltaPublic = computePublicDeltaState(beforePublic, afterPublic);
  const tensorInputs = {
    ...(confidenceInputs ?? comparison.after.measurement.confidenceInputs),
    crossEvidenceConsistency:
      confidenceInputs?.crossEvidenceConsistency ??
      comparison.after.measurement.confidenceInputs.observationCompleteness * 0.85,
  };
  const confidenceTensor = computeConfidenceTensor(tensorInputs);
  const meanConfidence = confidenceTensorScalar(confidenceTensor);
  const trajectory = computeTrajectoryVector(deltaPublic, confidenceTensor);
  const trajectoryWithAlias = {
    ...trajectory,
    confidence_weighted_magnitude: trajectory.confidenceWeightedMagnitude,
  };
  const signatures = classifyTrajectorySignatures(
    afterPublic,
    deltaPublic,
    trajectory,
    confidenceTensor.crossEvidenceConsistency,
  );
  const benchmarkDetail = summarizeBenchmarksDetailed(afterPublic, benchmarks);
  const scoreDeltas = scoreScaleDeltas(beforePublic, afterPublic);

  return {
    timestamp: comparison.after.measurement.measuredAt,
    orgId: comparison.orgId,
    label: comparison.after.measurement.label,
    state_vector: afterPublic,
    delta_state: deltaPublic,
    trajectory_vector: trajectoryWithAlias,
    benchmarks: {
      ...benchmarks,
      summary: benchmarkDetail.narrative,
      deltas: benchmarkDetail.deltas,
      bar_markers: scoresToBenchmarkPoints(afterPublic, benchmarks),
    },
    trajectory_signatures: signatures,
    trajectory_breakdown: buildTrajectoryBreakdown(deltaPublic, confidenceTensor, trajectoryWithAlias),
    projection: projectPublicState(afterPublic, deltaPublic, 2),
    risks: comparison.before.risks,
    interventions: comparison.before.interventions,
    evidence: {
      beforeConfidence: beforePublic.confidence,
      afterConfidence: afterPublic.confidence,
      meanConfidence,
      confidenceTensor,
    },
    before_after: { before: beforePublic, after: afterPublic },
    invariant_fitness: evaluateInvariantFitness(scoreDeltas, meanConfidence),
  };
}
