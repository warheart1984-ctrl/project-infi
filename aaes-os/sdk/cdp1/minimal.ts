import { RuntimeClient } from '../client/RuntimeClient.js';

export interface MinimalCDP1Result {
  baseline: unknown;
  perturbed: unknown;
  driftScore: number;
}

export async function runMinimalCDP1(
  client: RuntimeClient,
): Promise<MinimalCDP1Result> {
  const baseline = await client.execute({
    identity: { id: 'cdp1', type: 'agent', metadata: { role: 'cdp1-baseline' } },
    payload: { prompt: 'Hello, world.' },
  });

  const perturbed = await client.execute({
    identity: { id: 'cdp1', type: 'agent', metadata: { role: 'cdp1-perturbed' } },
    payload: { prompt: 'Hello, world!' },
  });

  if (!baseline.ok || !perturbed.ok) {
    throw new Error('CDP-1 minimal run failed due to invariant violation.');
  }

  const driftScore =
    JSON.stringify(baseline.result) === JSON.stringify(perturbed.result) ? 0 : 1;

  return {
    baseline: baseline.result,
    perturbed: perturbed.result,
    driftScore,
  };
}

/** In-process CDP-1 via CRK-1 reference runtime (no HTTP). */
export { runMinimalCDP1 as runMinimalLocal } from '../../benchmarks/cdp1/runMinimalCDP1.js';
