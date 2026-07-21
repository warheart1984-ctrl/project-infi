import { generateKeyPairSync } from 'node:crypto';

import { describe, expect, it } from 'vitest';

import {
  createAuditSigner,
  createAuditVerifier,
  signAuditPayload,
  signCanonicalAuditPacket,
  verifyAuditPayload,
  verifyCanonicalAuditPacket,
} from './signing.js';
import type { CanonicalAuditPacketInput } from './schema.js';
import { validateAuditPacket } from './validator.js';

describe('audit signing', () => {
  it('signs and verifies stable payloads regardless of object key order', () => {
    const { privateKey, publicKey } = generateKeyPairSync('ed25519');
    const privateKeyPem = privateKey.export({ format: 'pem', type: 'pkcs8' }).toString();
    const publicKeyPem = publicKey.export({ format: 'pem', type: 'spki' }).toString();

    const signer = createAuditSigner(privateKeyPem);
    const verifier = createAuditVerifier(publicKeyPem);

    const payloadA = {
      alpha: 1,
      nested: {
        bravo: true,
        charlie: ['x', 'y'],
      },
    };
    const payloadB = {
      nested: {
        charlie: ['x', 'y'],
        bravo: true,
      },
      alpha: 1,
    };

    const signature = signer(payloadA);
    expect(signature).toBe(signAuditPayload(payloadB, privateKeyPem));
    expect(verifier(payloadB, signature)).toBe(true);
    expect(verifyAuditPayload(payloadA, signature, publicKeyPem)).toBe(true);
  });

  it('signs and verifies canonical audit packets', () => {
    const { privateKey, publicKey } = generateKeyPairSync('ed25519');
    const privateKeyPem = privateKey.export({ format: 'pem', type: 'pkcs8' }).toString();
    const publicKeyPem = publicKey.export({ format: 'pem', type: 'spki' }).toString();

    const unsignedPacket: CanonicalAuditPacketInput = {
      version: '1.0',
      packetId: 'pkt-1',
      orgId: 'org-1',
      customerId: 'cust-1',
      requestId: 'req-1',
      createdAt: '2026-07-11T00:00:00.000Z',
      domain: 'routing',
      input: {
        prompt: 'route this request',
        context: { segment: 'enterprise' },
      },
      policy: {
        id: 'policy-1',
        name: 'Routing policy',
        dsl: 'require governance.level = full',
        compiledConstraints: { governance: 'full' },
      },
      decision: {
        modelId: 'model-1',
        outcome: { selected: 'model-1' },
        scores: { cost: 0.12 },
      },
      governance: {
        level: 'full',
        conformanceStatus: 'passing',
        driftRisk: 'low',
        lineageDepth: 7,
      },
      treasury: {
        price: 12.34,
        currency: 'USD',
        reserves: { platform: 2.5 },
      },
    };

    const signedPacket = signCanonicalAuditPacket(unsignedPacket, privateKeyPem);
    validateAuditPacket(signedPacket);
    expect(verifyCanonicalAuditPacket(signedPacket, publicKeyPem)).toBe(true);
  });
});
