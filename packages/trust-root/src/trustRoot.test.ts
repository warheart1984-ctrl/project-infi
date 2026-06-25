import { describe, expect, it, beforeEach } from 'vitest';

import {
  computeHTrustRoot,
  getTrustRoot,
  isMeasurement,
  isTrustRootSealed,
  resetTrustRootForTests,
  runEarlyBoot,
  sealTrustRoot,
  toUcrContext,
} from './index.js';

const KERNEL = 'sha3-256:1111111111111111111111111111111111111111111111111111111111111111';
const LAW = 'sha3-256:2222222222222222222222222222222222222222222222222222222222222222';
const CORRIDORS = 'sha3-256:3333333333333333333333333333333333333333333333333333333333333333';
const MANIFEST = 'sha3-256:4444444444444444444444444444444444444444444444444444444444444444';

describe('trust root measurements', () => {
  beforeEach(() => {
    resetTrustRootForTests();
  });

  it('validates canonical sha3-256 measurement strings', () => {
    expect(isMeasurement(KERNEL)).toBe(true);
    expect(isMeasurement('sha3-256:ABC')).toBe(false);
    expect(() => computeHTrustRoot({ hKernelImage: 'bad', hLawSpine: LAW, hCorridors: CORRIDORS, hBootManifest: MANIFEST })).toThrow(
      'invalid measurement',
    );
  });

  it('computes a deterministic trust root from fixed measurement order', () => {
    const first = computeHTrustRoot({
      hKernelImage: KERNEL,
      hLawSpine: LAW,
      hCorridors: CORRIDORS,
      hBootManifest: MANIFEST,
    });
    const second = computeHTrustRoot({
      hKernelImage: KERNEL,
      hLawSpine: LAW,
      hCorridors: CORRIDORS,
      hBootManifest: MANIFEST,
    });

    expect(first).toBe(second);
    expect(isMeasurement(first)).toBe(true);
  });

  it('seals exactly once and projects a UCR context', () => {
    const trustRoot = runEarlyBoot({
      hKernelImage: KERNEL,
      hLawSpine: LAW,
      hCorridors: CORRIDORS,
      hBootManifest: MANIFEST,
    }).trustRoot;

    expect(isTrustRootSealed()).toBe(true);
    expect(getTrustRoot()).toEqual(trustRoot);
    expect(toUcrContext(trustRoot)).toEqual({
      hashAlg: 'sha3-256',
      hLawSpine: LAW,
      hCorridors: CORRIDORS,
      hTrustRoot: trustRoot.hTrustRoot,
    });
    expect(() => sealTrustRoot(trustRoot)).toThrow('already sealed');
  });
});
