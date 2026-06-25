import { createTestRuntime } from '../../tests/helpers/runtime.js';

export interface DriftResult {
  baseline: unknown;
  perturbed: unknown;
  driftScore: number;
}

/** Minimal CDP-1 continuity slice — punctuation perturbation on identical runtime. */
export async function runMinimalCDP1(): Promise<DriftResult> {
  const { runtime } = createTestRuntime();

  const baselinePayload = { prompt: 'Hello, world.' };
  const perturbedPayload = { prompt: 'Hello, world!' };

  const baseline = await runtime.run({ payload: baselinePayload });
  const perturbed = await runtime.run({ payload: perturbedPayload });

  if (baseline.status !== 'completed' || perturbed.status !== 'completed') {
    throw new Error('CDP-1 minimal run failed due to invariant violation or runtime fault.');
  }

  const baselineOut = baseline.output;
  const perturbedOut = perturbed.output;

  const driftScore =
    JSON.stringify(baselineOut) === JSON.stringify(perturbedOut) ? 0 : 1;

  return {
    baseline: baselineOut,
    perturbed: perturbedOut,
    driftScore,
  };
}
