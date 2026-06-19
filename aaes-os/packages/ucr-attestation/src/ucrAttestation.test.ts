import { beforeEach, describe, expect, it } from 'vitest';

import { resetTrustRootForTests, runEarlyBoot } from '@aaes-os/trust-root';

import {
  ERR_BOOT_NOT_SEALED,
  ERR_SIGNATURE_INVALID,
  ERR_TOKEN_EXPIRED,
  ERR_TRUST_ROOT_MISMATCH,
  getRegisteredUcrHandle,
  issueAttestationFromSealedTrust,
  issueAttestationToken,
  resetUcrRegistrationForTests,
  ucrRegister,
} from './index.js';

const KERNEL = 'sha3-256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
const LAW = 'sha3-256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';
const CORRIDORS = 'sha3-256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc';
const MANIFEST = 'sha3-256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd';

describe('UCR attestation', () => {
  beforeEach(() => {
    resetTrustRootForTests();
    resetUcrRegistrationForTests();
  });

  it('refuses registration before boot is sealed', () => {
    const token = issueAttestationToken({
      ucrInstanceId: 'ucr-1',
      buildFingerprint: 'build-a',
      lawKey: '00000000000000000000000000000001',
      trustRoot: KERNEL,
      corridorsHash: CORRIDORS,
      lawSpineHash: LAW,
      expiresAt: new Date(Date.now() + 60_000).toISOString(),
    });

    expect(ucrRegister(token)).toMatchObject({ outcome: 'REFUSED', reasonCode: ERR_BOOT_NOT_SEALED });
  });

  it('issues a sealed-trust token and registers a UCR handle', () => {
    const boot = runEarlyBoot({ hKernelImage: KERNEL, hLawSpine: LAW, hCorridors: CORRIDORS, hBootManifest: MANIFEST });
    const token = issueAttestationFromSealedTrust({
      ucrInstanceId: 'ucr-live',
      buildFingerprint: 'build-live',
      expiresAt: new Date(Date.now() + 60_000).toISOString(),
    });

    expect(token.trustRoot).toBe(boot.trustRoot.hTrustRoot);
    const result = ucrRegister(token);
    expect(result.outcome).toBe('OK');
    expect(result.ucrHandle).toBeTruthy();
    expect(getRegisteredUcrHandle()).toBe(result.ucrHandle);
  });

  it('uses deterministic refusal ordering for expired, bad signature, and mismatched trust roots', () => {
    const boot = runEarlyBoot({ hKernelImage: KERNEL, hLawSpine: LAW, hCorridors: CORRIDORS, hBootManifest: MANIFEST });
    const expired = issueAttestationFromSealedTrust({
      ucrInstanceId: 'ucr-expired',
      buildFingerprint: 'build-expired',
      expiresAt: new Date(Date.now() - 1_000).toISOString(),
    });
    expect(ucrRegister(expired)).toMatchObject({ outcome: 'REFUSED', reasonCode: ERR_TOKEN_EXPIRED });

    const badSignature = { ...issueAttestationFromSealedTrust({
      ucrInstanceId: 'ucr-bad-sig',
      buildFingerprint: 'build-bad-sig',
      expiresAt: new Date(Date.now() + 60_000).toISOString(),
    }), signature: '00' };
    expect(ucrRegister(badSignature)).toMatchObject({ outcome: 'REFUSED', reasonCode: ERR_SIGNATURE_INVALID });

    const mismatch = issueAttestationToken({
      ucrInstanceId: 'ucr-mismatch',
      buildFingerprint: 'build-mismatch',
      lawKey: '00000000000000000000000000000001',
      trustRoot: boot.trustRoot.hLawSpine,
      corridorsHash: boot.trustRoot.hCorridors,
      lawSpineHash: boot.trustRoot.hLawSpine,
      expiresAt: new Date(Date.now() + 60_000).toISOString(),
    });
    expect(ucrRegister(mismatch)).toMatchObject({ outcome: 'REFUSED', reasonCode: ERR_TRUST_ROOT_MISMATCH });
  });
});
