import crypto from 'node:crypto';

import type { CanonicalAuditPacket, CanonicalAuditPacketInput } from './schema.js';
import { validateUnsignedAuditPacket } from './validator.js';

export interface AuditSigningKeys {
  privateKeyPem: string;
  publicKeyPem: string;
}

export type AuditSigner = (payload: unknown) => string;
export type AuditVerifier = (payload: unknown, signature: string) => boolean;

export function readAuditSigningKeysFromEnv(env: NodeJS.ProcessEnv = process.env): AuditSigningKeys | null {
  const privateKeyPem = readEnvValue(env.AUDIT_PRIVATE_KEY) ?? readEnvValue(env.AUDIT_PRIVATE_KEY_PEM);
  const publicKeyPem = readEnvValue(env.AUDIT_PUBLIC_KEY) ?? readEnvValue(env.AUDIT_PUBLIC_KEY_PEM);
  if (!privateKeyPem || !publicKeyPem) {
    return null;
  }

  return {
    privateKeyPem,
    publicKeyPem,
  };
}

export function signAuditPayload(payload: unknown, privateKeyPem: string): string {
  const signature = crypto.sign(null, Buffer.from(canonicalizeJson(payload)), privateKeyPem);
  return signature.toString('base64');
}

export function verifyAuditPayload(payload: unknown, signature: string, publicKeyPem: string): boolean {
  return crypto.verify(null, Buffer.from(canonicalizeJson(payload)), publicKeyPem, Buffer.from(signature, 'base64'));
}

export function createAuditSigner(privateKeyPem: string): AuditSigner {
  return (payload: unknown) => signAuditPayload(payload, privateKeyPem);
}

export function createAuditVerifier(publicKeyPem: string): AuditVerifier {
  return (payload: unknown, signature: string) => verifyAuditPayload(payload, signature, publicKeyPem);
}

export function signCanonicalAuditPacket(
  packet: CanonicalAuditPacketInput,
  privateKeyPem: string,
): CanonicalAuditPacket {
  validateUnsignedAuditPacket(packet);
  const signature = signAuditPayload(packet, privateKeyPem);
  return {
    ...packet,
    signature: {
      algorithm: 'Ed25519',
      value: signature,
    },
  };
}

export function verifyCanonicalAuditPacket(packet: CanonicalAuditPacket, publicKeyPem: string): boolean {
  const { signature, ...unsignedPacket } = packet;
  return verifyAuditPayload(unsignedPacket, signature.value, publicKeyPem);
}

function canonicalizeJson(value: unknown): string {
  const normalized = normalizeJsonValue(value);
  const json = JSON.stringify(normalized);
  if (json === undefined) {
    throw new TypeError('Cannot sign an undefined audit payload');
  }
  return json;
}

function normalizeJsonValue(value: unknown, seen = new WeakSet<object>()): unknown {
  if (value instanceof Date) {
    return value.toISOString();
  }
  if (typeof value === 'bigint' || typeof value === 'symbol' || typeof value === 'function') {
    throw new TypeError('Unsupported audit payload value');
  }
  if (value === null || typeof value !== 'object') {
    return value;
  }

  if (Array.isArray(value)) {
    return value.map((item) => normalizeJsonValue(item, seen));
  }

  if (seen.has(value)) {
    throw new TypeError('Cannot sign cyclic audit payloads');
  }
  seen.add(value);

  const normalized: Record<string, unknown> = {};
  for (const key of Object.keys(value).sort()) {
    normalized[key] = normalizeJsonValue((value as Record<string, unknown>)[key], seen);
  }

  seen.delete(value);
  return normalized;
}

function readEnvValue(value: string | undefined): string | null {
  if (!value) {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}
