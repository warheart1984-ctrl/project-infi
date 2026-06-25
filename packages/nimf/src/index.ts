import type { MRIOutputV2 } from '@aaes-os/mri-instrument';

type Dimension = 'continuity' | 'governance' | 'memory' | 'coordination' | 'confidence';
type DimensionVector = Record<Dimension, number>;

export interface NimfStateModel {
  velocity: DimensionVector;
  acceleration: DimensionVector;
  volatility: number;
  confidenceWeightedRisk: number;
}

export interface NimfForecast extends NimfStateModel {
  horizon: number;
  projectedStates: MRIOutputV2['state_vector'][];
  signature: string;
}

export function modelStateTransition(mri: MRIOutputV2): NimfStateModel {
  const velocity = { ...mri.delta_state };
  const acceleration = mapVector(velocity, (value) => Number((value * mri.evidence.meanConfidence).toFixed(4)));
  const values = Object.values(velocity);
  const volatility = Number(Math.sqrt(values.reduce((sum, value) => sum + value * value, 0)).toFixed(4));
  const negativeMotion = values.filter((value) => value < 0).reduce((sum, value) => sum + Math.abs(value), 0);
  const confidenceWeightedRisk = Number((negativeMotion * mri.evidence.meanConfidence).toFixed(4));
  return { velocity, acceleration, volatility, confidenceWeightedRisk };
}

export function forecastTrajectory(mri: MRIOutputV2, horizon: number): NimfForecast {
  const model = modelStateTransition(mri);
  const projectedStates = Array.from({ length: horizon }, (_, index) => {
    const step = index + 1;
    return mapVector(mri.state_vector, (value, dimension) =>
      clampScore(value + model.velocity[dimension] * 100 * step + model.acceleration[dimension] * 50 * step),
    );
  });
  return {
    ...model,
    horizon,
    projectedStates,
    signature: mri.trajectory_signatures[0] ?? 'stable_continuity_stable_governance',
  };
}

function mapVector<T extends Record<Dimension, number>>(
  vector: T,
  mapper: (value: number, dimension: Dimension) => number,
): DimensionVector {
  return {
    continuity: mapper(vector.continuity, 'continuity'),
    governance: mapper(vector.governance, 'governance'),
    memory: mapper(vector.memory, 'memory'),
    coordination: mapper(vector.coordination, 'coordination'),
    confidence: mapper(vector.confidence, 'confidence'),
  };
}

function clampScore(value: number): number {
  return Number(Math.max(0, Math.min(100, value)).toFixed(2));
}
