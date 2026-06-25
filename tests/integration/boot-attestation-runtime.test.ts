import { describe, expect, it } from 'vitest';

import { initializeRuntime } from '@aaes-os/runtime-law-spine';
import { UCRRuntime } from '@aaes-os/ucr-runtime';

describe('boot attestation runtime integration', () => {
  it('boots, registers UCR custody, and runs the governed runtime', async () => {
    const init = initializeRuntime({
      trustRootInput: {
        hKernelImage: 'sha3-256:1000000000000000000000000000000000000000000000000000000000000000',
        hLawSpine: 'sha3-256:2000000000000000000000000000000000000000000000000000000000000000',
        hCorridors: 'sha3-256:3000000000000000000000000000000000000000000000000000000000000000',
        hBootManifest: 'sha3-256:4000000000000000000000000000000000000000000000000000000000000000',
      },
      corridors: [{ corridorId: 'prod-ops', capabilities: ['execute'] }],
      conformanceLevel: 2,
      ucrInstanceId: 'ucr-integration',
      buildFingerprint: 'build-integration',
    });
    const runtime = new UCRRuntime({ enablePatches: true, demoSchedule: ['good'] });
    const run = await runtime.run({ kind: 'integration', payload: { ok: true } });

    expect(init.allowed).toBe(true);
    expect(init.registration.outcome).toBe('OK');
    expect(run.status).toBe('completed');
    expect(run.faults).toHaveLength(0);
  });
});
