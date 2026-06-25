import { createCrk1Runtime } from '../../tests/helpers/crk1Runtime.js';

export interface DriftResult {
  baseline: unknown;
  perturbed: unknown;
  driftScore: number;
}

/** Minimal CDP-1 continuity slice — punctuation perturbation on CRK-1 reference runtime. */
export async function runMinimalCDP1(): Promise<DriftResult> {
  const baselinePayload = { prompt: 'Hello, world.' };
  const perturbedPayload = { prompt: 'Hello, world!' };

  const r1 = createCrk1Runtime();
  const baseline = await r1.execute({ payload: baselinePayload });

  const r2 = createCrk1Runtime();
  const perturbed = await r2.execute({ payload: perturbedPayload });

  if (!baseline.ok || !perturbed.ok) {
    throw new Error('CDP-1 minimal run failed due to invariant violation.');
  }

  const baselineOut = baseline.result;
  const perturbedOut = perturbed.result;

  const driftScore =
    JSON.stringify(baselineOut) === JSON.stringify(perturbedOut) ? 0 : 1;

  return {
    baseline: baselineOut,
    perturbed: perturbedOut,
    driftScore,
  };
}
