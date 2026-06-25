import { describe, expect, it } from 'vitest';

import {
  buildMRIOutputV2,
  evaluateInvariantFitness,
} from './mriV2.js';
import { computeConfidenceTensor, confidenceTensorScalar } from './confidenceTensor.js';
import {
  computeTrajectoryVector,
  classifyTrajectorySignatures,
} from './trajectory.js';
import { computePublicDeltaState, summarizeBenchmarks } from './benchmark.js';
import { PILOT_AFTER, PILOT_BEFORE, runMRIComparison } from './index.js';

const confidenceInputs = {
  observationCompleteness: 0.85,
  dataQuality: 0.8,
  sourceReliability: 0.78,
  temporalFreshness: 0.82,
  crossEvidenceConsistency: 0.76,
};

const benchmarks = {
  industryAverage: {
    continuity: 61,
    governance: 59,
    memory: 64,
    coordination: 57,
  },
  topQuartile: {
    continuity: 78,
    governance: 74,
    memory: 82,
    coordination: 71,
  },
  previousMeasurement: {
    continuity: 64,
    governance: 72,
    memory: 64,
    coordination: 65,
  },
};

describe('MRI v0.2 trajectory layer', () => {
  it('computes T(t) as confidence-weighted normalized delta', () => {
    const delta = {
      continuity: 0.1,
      governance: -0.04,
      memory: 0.11,
      coordination: -0.02,
      confidence: 0,
    };
    const tensor = computeConfidenceTensor(confidenceInputs);
    const t = computeTrajectoryVector(delta, tensor);
    expect(t.continuity).toBeCloseTo(0.1 * 0.85, 5);
    expect(t.magnitude).toBeGreaterThan(0);
    expect(t.confidenceWeightedMagnitude).toBeLessThanOrEqual(t.magnitude);
  });

  it('buildMRIOutputV2 includes benchmarks, trajectory, and signatures', () => {
    const result = runMRIComparison(PILOT_BEFORE, PILOT_AFTER);
    const v2 = buildMRIOutputV2(result, benchmarks, confidenceInputs);

    expect(v2.state_vector.continuity).toBeGreaterThan(v2.before_after.before.continuity);
    expect(v2.delta_state.continuity).toBeGreaterThan(0);
    expect(v2.trajectory_vector.magnitude).toBeGreaterThanOrEqual(0);
    expect(v2.benchmarks.summary).toContain('industry');
    expect(v2.benchmarks.bar_markers.continuity).toEqual(
      expect.objectContaining({
        current: expect.any(Number),
        previous: expect.any(Number),
        industry: expect.any(Number),
        topQuartile: expect.any(Number),
      }),
    );
    expect(v2.trajectory_signatures.length).toBeGreaterThan(0);
    expect(v2.trajectory_breakdown).toHaveLength(4);
    expect(v2.projection).toHaveLength(3);
    expect(v2.evidence.confidenceTensor.crossEvidenceConsistency).toBeGreaterThan(0);
  });

  it('evaluateInvariantFitness promotes on broad improvement', () => {
    const fitness = evaluateInvariantFitness({
      continuity: 8,
      governance: 6,
      memory: 9,
      coordination: 4,
      confidence: 0,
    }, 0.8);
    expect(fitness.verdict).toBe('promote');
    expect(fitness.improvedDimensions.length).toBeGreaterThanOrEqual(3);
  });

  it('classifies contradictory subsystem motion', () => {
    const state = {
      continuity: 70,
      governance: 68,
      memory: 72,
      coordination: 63,
      confidence: 81,
    };
    const delta = {
      continuity: 0.08,
      governance: -0.06,
      memory: 0.07,
      coordination: -0.05,
      confidence: 0,
    };
    const tensor = computeConfidenceTensor(confidenceInputs);
    const trajectory = computeTrajectoryVector(delta, tensor);
    const ids = classifyTrajectorySignatures(state, delta, trajectory, 0.76);
    expect(ids).toContain('contradictory_subsystem_motion');
  });

  it('computePublicDeltaState normalizes point deltas to unit scale', () => {
    const prev = { continuity: 64, governance: 72, memory: 64, coordination: 65, confidence: 74 };
    const curr = { continuity: 72, governance: 68, memory: 75, coordination: 63, confidence: 81 };
    const norm = computePublicDeltaState(prev, curr);
    expect(norm.continuity).toBeCloseTo(0.08, 5);
    expect(norm.governance).toBeCloseTo(-0.04, 5);
  });

  it('confidenceTensorScalar averages tensor axes', () => {
    const tensor = computeConfidenceTensor(confidenceInputs);
    expect(confidenceTensorScalar(tensor)).toBeCloseTo(0.802, 2);
  });

  it('summarizeBenchmarks produces readable summary', () => {
    const summary = summarizeBenchmarks(
      { continuity: 72, governance: 68, memory: 75, coordination: 63, confidence: 81 },
      benchmarks,
    );
    expect(summary).toMatch(/industry/i);
    expect(summary).toMatch(/quartile/i);
  });
});
