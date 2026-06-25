import { createHash, randomUUID } from 'node:crypto';

import {
  asMeasurement,
  getTrustRoot,
  isTrustRootSealed,
  toUcrContext,
  type Measurement,
} from '@aaes-os/trust-root';

export const ERR_LAW_KEY_INVALID = 1001;
export const ERR_TRUST_ROOT_MISMATCH = 1006;
export const ERR_BOOT_NOT_SEALED = 1007;
export const ERR_TOKEN_EXPIRED = 1008;
export const ERR_CORRIDORS_HASH_MISMATCH = 1009;
export const ERR_LAW_SPINE_HASH_MISMATCH = 1010;
export const ERR_SIGNATURE_INVALID = 1011;

export type RegisterOutcome = 'OK' | 'REFUSED';

export interface UCRAttestationToken {
  tokenId: string;
  ucrInstanceId: string;
  buildFingerprint: string;
  lawKey: string;
  trustRoot: Measurement;
  corridorsHash: Measurement;
  lawSpineHash: Measurement;
  issuedAt: string;
  expiresAt: string;
  nonce: string;
  signature: string;
}

export interface UCRRegisterResult {
  outcome: RegisterOutcome;
  ucrHandle?: string;
  reasonCode?: number;
  reasonDetail?: string;
  metadata?: Record<string, string>;
}

export interface IssueAttestationTokenInput {
  tokenId?: string;
  ucrInstanceId: string;
  buildFingerprint: string;
  lawKey?: string;
  trustRoot: string;
  corridorsHash: string;
  lawSpineHash: string;
  issuedAt?: string;
  expiresAt: string;
  nonce?: string;
}

export interface IssueAttestationFromSealedTrustInput {
  ucrInstanceId: string;
  buildFingerprint: string;
  expiresAt?: string;
  lawKey?: string;
}

const ATTEST_DOMAIN = 'AAES-UCR-ATTEST-v1\0';
const DEFAULT_LAW_KEY = '00000000000000000000000000000001';
let registeredUcrHandle: string | undefined;

export function issueAttestationToken(input: IssueAttestationTokenInput): UCRAttestationToken {
  if (!input.ucrInstanceId.trim()) {
    throw new Error('ucrInstanceId is required');
  }
  if (!input.buildFingerprint.trim()) {
    throw new Error('buildFingerprint is required');
  }
  const token: UCRAttestationToken = {
    tokenId: input.tokenId ?? randomUUID(),
    ucrInstanceId: input.ucrInstanceId,
    buildFingerprint: input.buildFingerprint,
    lawKey: input.lawKey ?? DEFAULT_LAW_KEY,
    trustRoot: asMeasurement(input.trustRoot),
    corridorsHash: asMeasurement(input.corridorsHash),
    lawSpineHash: asMeasurement(input.lawSpineHash),
    issuedAt: input.issuedAt ?? new Date().toISOString(),
    expiresAt: input.expiresAt,
    nonce: input.nonce ?? randomUUID().replaceAll('-', ''),
    signature: '',
  };
  return { ...token, signature: placeholderSignature(token) };
}

export function issueAttestationFromSealedTrust(input: IssueAttestationFromSealedTrustInput): UCRAttestationToken {
  const sealed = getTrustRoot();
  return issueAttestationToken({
    ucrInstanceId: input.ucrInstanceId,
    buildFingerprint: input.buildFingerprint,
    lawKey: input.lawKey,
    trustRoot: sealed.hTrustRoot,
    corridorsHash: sealed.hCorridors,
    lawSpineHash: sealed.hLawSpine,
    expiresAt: input.expiresAt ?? new Date(Date.now() + 5 * 60_000).toISOString(),
  });
}

export function ucrRegister(token: UCRAttestationToken): UCRRegisterResult {
  if (!isTrustRootSealed()) {
    return refused(ERR_BOOT_NOT_SEALED, 'trust root is not sealed');
  }
  if (Date.parse(token.expiresAt) <= Date.now()) {
    return refused(ERR_TOKEN_EXPIRED, 'attestation token expired');
  }
  if (!validateLawKey(token.lawKey)) {
    return refused(ERR_LAW_KEY_INVALID, 'law key is invalid');
  }
  if (!token.signature || token.signature !== placeholderSignature(token)) {
    return refused(ERR_SIGNATURE_INVALID, 'signature is invalid');
  }

  const sealed = getTrustRoot();
  const context = toUcrContext(sealed);
  if (token.trustRoot !== sealed.hTrustRoot || context.hTrustRoot !== token.trustRoot) {
    return refused(ERR_TRUST_ROOT_MISMATCH, 'trust root mismatch');
  }
  if (token.corridorsHash !== sealed.hCorridors) {
    return refused(ERR_CORRIDORS_HASH_MISMATCH, 'corridors hash mismatch');
  }
  if (token.lawSpineHash !== sealed.hLawSpine) {
    return refused(ERR_LAW_SPINE_HASH_MISMATCH, 'law spine hash mismatch');
  }

  registeredUcrHandle = randomUUID();
  return {
    outcome: 'OK',
    ucrHandle: registeredUcrHandle,
    metadata: {
      tokenId: token.tokenId,
      ucrInstanceId: token.ucrInstanceId,
      trustRoot: token.trustRoot,
    },
  };
}

export function getRegisteredUcrHandle(): string | undefined {
  return registeredUcrHandle;
}

export function resetUcrRegistrationForTests(): void {
  registeredUcrHandle = undefined;
}

export function placeholderSignature(token: Omit<UCRAttestationToken, 'signature'>): string {
  const payload = [
    ATTEST_DOMAIN,
    token.tokenId,
    token.ucrInstanceId,
    token.buildFingerprint,
    token.lawKey,
    token.trustRoot,
    token.corridorsHash,
    token.lawSpineHash,
    token.issuedAt,
    token.expiresAt,
    token.nonce,
  ].join('|');
  return createHash('sha3-256').update(payload, 'utf8').digest('hex');
}

function validateLawKey(lawKey: string): boolean {
  return /^[0-9a-f]{32}$/.test(lawKey) && lawKey !== '00000000000000000000000000000000';
}

function refused(reasonCode: number, reasonDetail: string): UCRRegisterResult {
  return { outcome: 'REFUSED', reasonCode, reasonDetail };
}
