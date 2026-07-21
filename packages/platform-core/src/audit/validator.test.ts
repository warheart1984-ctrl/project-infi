import { describe, expect, it } from 'vitest';

import { AuditPacketValidationError, isCanonicalAuditPacket, isCanonicalAuditPacketInput, validateAuditPacket, validateUnsignedAuditPacket } from './validator.js';
import type { CanonicalAuditPacket, CanonicalAuditPacketInput } from './schema.js';

describe('audit packet validator', () => {
  it('accepts a valid unsigned canonical packet', () => {
    const packet: CanonicalAuditPacketInput = {
      version: '1.0',
      packetId: 'pkt-1',
      orgId: 'org-1',
      requestId: 'req-1',
      createdAt: '2026-07-11T00:00:00.000Z',
      domain: 'pricing',
      input: {},
      policy: {
        id: 'policy-1',
        name: 'Pricing policy',
        dsl: 'require plan.id = pro',
        compiledConstraints: [],
      },
      decision: {
        modelId: 'model-1',
        outcome: { status: 'APPROVED' },
      },
      governance: {
        level: 'enhanced',
      },
    };

    expect(isCanonicalAuditPacketInput(packet)).toBe(true);
    expect(() => validateUnsignedAuditPacket(packet)).not.toThrow();
  });

  it('accepts a valid signed canonical packet', () => {
    const packet: CanonicalAuditPacket = {
      version: '1.0',
      packetId: 'pkt-1',
      orgId: 'org-1',
      requestId: 'req-1',
      createdAt: '2026-07-11T00:00:00.000Z',
      domain: 'routing',
      input: {},
      policy: {
        id: 'policy-1',
        name: 'Routing policy',
        dsl: 'require governance.level = full',
        compiledConstraints: { governance: 'full' },
      },
      decision: {
        modelId: 'model-1',
        outcome: { status: 'APPROVED' },
      },
      governance: {
        level: 'full',
      },
      signature: {
        algorithm: 'Ed25519',
        value: 'MDEwDQYJKoZIhvcNAQEBBQAE',
      },
    };

    expect(isCanonicalAuditPacket(packet)).toBe(true);
    expect(() => validateAuditPacket(packet)).not.toThrow();
  });

  it('rejects malformed packets', () => {
    expect(() => validateUnsignedAuditPacket({
      version: '2.0',
    } as CanonicalAuditPacketInput)).toThrow(AuditPacketValidationError);
  });
});
