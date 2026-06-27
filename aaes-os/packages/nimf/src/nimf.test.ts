import { describe, expect, it } from 'vitest';

import { buildMRIOutputV2, PILOT_AFTER, PILOT_BEFORE, PILOT_BENCHMARKS, runMRIComparison } from '@aaes-os/mri-instrument';
import { forecastTrajectory, modelStateTransition } from './index.js';

describe('NIMF institutional physics', () => {
  it('models velocity, acceleration, volatility, and confidence-weighted risk from MRI v0.2', () => {
    const mri = buildMRIOutputV2(runMRIComparison(PILOT_BEFORE, PILOT_AFTER), PILOT_BENCHMARKS);
    const model = modelStateTransition(mri);

    expect(model.velocity.continuity).toBe(mri.delta_state.continuity);
    expect(model.volatility).toBeGreaterThanOrEqual(0);
    expect(model.confidenceWeightedRisk).toBeGreaterThanOrEqual(0);
  });

  it('forecasts trajectory over the requested horizon', () => {
    const mri = buildMRIOutputV2(runMRIComparison(PILOT_BEFORE, PILOT_AFTER), PILOT_BENCHMARKS);
    const forecast = forecastTrajectory(mri, 3);

    expect(forecast.horizon).toBe(3);
    expect(forecast.projectedStates).toHaveLength(3);
    expect(forecast.signature).toBeTruthy();
  });
});
