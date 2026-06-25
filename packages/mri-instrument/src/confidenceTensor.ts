import type { ConfidenceInputs } from './index.js';

/** Five-dimensional reliability model for trajectory weighting (MRI v0.2). */
export type ConfidenceTensor = {
  observationCompleteness: number;
  dataQuality: number;
  sourceReliability: number;
  temporalFreshness: number;
  crossEvidenceConsistency: number;
};

export type ConfidenceTensorInputs = ConfidenceInputs & {
  crossEvidenceConsistency: number;
};

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}

/** Build C from instrument inputs; each axis is in [0, 1]. */
export function computeConfidenceTensor(inputs: ConfidenceTensorInputs): ConfidenceTensor {
  return {
    observationCompleteness: clamp01(inputs.observationCompleteness),
    dataQuality: clamp01(inputs.dataQuality),
    sourceReliability: clamp01(inputs.sourceReliability),
    temporalFreshness: clamp01(inputs.temporalFreshness),
    crossEvidenceConsistency: clamp01(inputs.crossEvidenceConsistency),
  };
}

/** Scalar summary for UI (mean of tensor axes). */
export function confidenceTensorScalar(tensor: ConfidenceTensor): number {
  const values = Object.values(tensor);
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}
