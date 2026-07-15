import { describe, expect, it } from 'vitest';
import {
  isExternalIntegrationEvidenceIndex,
  summarizeExternalIntegrationEvidence,
  type ExternalIntegrationEvidenceIndex,
} from '../../tools/external-integration-evidence.js';

describe('external integration evidence', () => {
  it('validates and summarizes real-service evidence packets', () => {
    const packet: ExternalIntegrationEvidenceIndex = {
      generatedAt: '2026-07-13T00:00:00.000Z',
      workspace: 'E:/project-infi',
      status: 'verified',
      aggregateHash: 'hash',
      observations: [
        {
          id: 'github-origin-remote',
          service: 'GitHub',
          target: 'https://github.com/warheart1984-ctrl/project-infi.git',
          mode: 'git-ls-remote',
          status: 'verified',
          checkedAt: '2026-07-13T00:00:00.000Z',
          evidenceHash: 'github-hash',
          command: 'git ls-remote origin HEAD',
          observed: {
            ref: 'HEAD',
            commit: '0123456789abcdef0123456789abcdef01234567',
          },
          blockers: [],
        },
        {
          id: 'npm-registry-toolchain',
          service: 'npm Registry',
          target: 'pnpm',
          mode: 'registry-metadata-fetch',
          status: 'verified',
          checkedAt: '2026-07-13T00:00:00.000Z',
          evidenceHash: 'npm-hash',
          endpoint: 'https://registry.npmjs.org/pnpm',
          observed: {
            requestedPackage: 'pnpm',
            workspacePackageManager: 'pnpm@10.15.0',
            httpStatus: 200,
            registryName: 'pnpm',
            latestVersion: '10.0.0',
          },
          blockers: [],
        },
      ],
    };

    expect(isExternalIntegrationEvidenceIndex(packet)).toBe(true);
    expect(summarizeExternalIntegrationEvidence(packet)).toEqual({
      verifiedCount: 2,
      blockedCount: 0,
      services: ['GitHub', 'npm Registry'],
    });
  });

  it('rejects malformed packets instead of treating placeholders as evidence', () => {
    expect(
      isExternalIntegrationEvidenceIndex({
        status: 'verified',
        observations: [
          {
            id: 'placeholder',
            service: 'GitHub',
            status: 'adapter-contract-ready',
          },
        ],
      }),
    ).toBe(false);
  });
});
