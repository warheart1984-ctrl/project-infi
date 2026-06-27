import { beforeEach, describe, expect, it } from 'vitest';

import { resetTrustRootForTests, runEarlyBoot } from '@aaes-os/trust-root';

import { RuntimeLawSpine, initializeRuntime } from './index.js';

const KERNEL = `sha3-256:${'a'.repeat(64)}`;
const LAW = `sha3-256:${'b'.repeat(64)}`;
const CORRIDORS = `sha3-256:${'c'.repeat(64)}`;
const MANIFEST = `sha3-256:${'d'.repeat(64)}`;

describe('runtime law spine', () => {
  beforeEach(() => {
    resetTrustRootForTests();
  });

  it('admits known corridors and quarantines anomalous corridors at L3', () => {
    runEarlyBoot({ hKernelImage: KERNEL, hLawSpine: LAW, hCorridors: CORRIDORS, hBootManifest: MANIFEST });
    const spine = new RuntimeLawSpine({
      corridors: [{ corridorId: 'prod-ops', capabilities: ['execute'] }],
      conformanceLevel: 3,
      lawEvolutionCorridorId: 'law-evolution',
    });

    expect(spine.admit({ corridorId: 'prod-ops', requestedCapabilities: ['execute'] })).toMatchObject({ admitted: true });
    expect(spine.admit({ corridorId: 'missing', requestedCapabilities: ['execute'] })).toMatchObject({ admitted: false, reasonCode: 'CORRIDOR_UNKNOWN' });
    expect(spine.isQuarantined('missing')).toBe(true);
  });

  it('allows law mutation only through the law evolution corridor', () => {
    runEarlyBoot({ hKernelImage: KERNEL, hLawSpine: LAW, hCorridors: CORRIDORS, hBootManifest: MANIFEST });
    const spine = new RuntimeLawSpine({
      corridors: [
        { corridorId: 'prod-ops', capabilities: ['execute', 'mutate_law'] },
        { corridorId: 'law-evolution', capabilities: ['mutate_law'] },
      ],
      conformanceLevel: 3,
      lawEvolutionCorridorId: 'law-evolution',
    });

    expect(spine.admit({ corridorId: 'prod-ops', requestedCapabilities: ['mutate_law'], mutationKind: 'law' })).toMatchObject({
      admitted: false,
      reasonCode: 'LAW_EVOLUTION_CORRIDOR_REQUIRED',
    });
    expect(spine.admit({ corridorId: 'law-evolution', requestedCapabilities: ['mutate_law'], mutationKind: 'law' })).toMatchObject({
      admitted: true,
    });
  });

  it('returns a runtime initialization result bound to the sealed trust root', () => {
    const result = initializeRuntime({
      trustRootInput: { hKernelImage: KERNEL, hLawSpine: LAW, hCorridors: CORRIDORS, hBootManifest: MANIFEST },
      corridors: [{ corridorId: 'prod-ops', capabilities: ['execute'] }],
      conformanceLevel: 2,
      ucrInstanceId: 'ucr-init',
      buildFingerprint: 'build-init',
    });

    expect(result.allowed).toBe(true);
    expect(result.boot.bootResult).toBe('OK');
    expect(result.registration.outcome).toBe('OK');
    expect(result.runtimeContext.hTrustRoot).toBe(result.boot.trustRoot.hTrustRoot);
  });
});
