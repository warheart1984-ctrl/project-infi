import { generateKeyPairSync } from 'node:crypto';
import { mkdtempSync, rmSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { signCanonicalAuditPacket } from '@aaes-os/platform-core';

import { CepArtifactStore, verifyCepArtifactSignature } from './cepArtifactStore.js';

describe('CepArtifactStore', () => {
  it('persists canonical audit packets with a signature and verifies them on read', () => {
    const tempDir = mkdtempSync(path.join(os.tmpdir(), 'ops-console-cep-'));
    const storePath = path.join(tempDir, 'cep-artifacts.jsonl');
    const { privateKey, publicKey } = generateKeyPairSync('ed25519');
    const privateKeyPem = privateKey.export({ format: 'pem', type: 'pkcs8' }).toString();
    const publicKeyPem = publicKey.export({ format: 'pem', type: 'spki' }).toString();

    try {
      const store = new CepArtifactStore({
        filePath: storePath,
        env: {
          AUDIT_PUBLIC_KEY: publicKeyPem,
        },
      });

      const signedPacket = signCanonicalAuditPacket(
        {
          version: '1.0',
          packetId: 'pkt-1',
          orgId: 'org-1',
          customerId: 'cust-1',
          requestId: 'req-1',
          createdAt: '2026-07-11T00:00:00.000Z',
          domain: 'routing',
          input: {
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
            outcome: { status: 'APPROVED' },
          },
          governance: {
            level: 'full',
          },
        },
        privateKeyPem,
      );

      const record = store.append({
        kind: 'decision',
        title: 'Signed decision',
        source: 'unit-test',
        organizationId: 'org-1',
        payload: signedPacket,
      });

      expect(record.signature).toBe(signedPacket.signature.value);
      expect(store.list(storePath, 'org-1')).toHaveLength(1);
      expect(verifyCepArtifactSignature(record, publicKeyPem)).toBe(true);
    } finally {
      rmSync(tempDir, { recursive: true, force: true });
    }
  });
});
