import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdtempSync, readFileSync, copyFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

function readReleaseManifest(): { artifacts?: string[] } {
  return JSON.parse(readFileSync(path.join(process.cwd(), 'release', 'release-manifest.json'), 'utf8')) as {
    artifacts?: string[];
  };
}

function sha256(filePath: string): string {
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

const COMMITTED_RELEASE_FILES = [
  'release/checksums.json',
  'release/signature.json',
  'release/constitutional-release-receipt.json',
  'release/bundle/checksums.json',
  'release/bundle/release-package.json',
  'release/bundle/signature.json',
  'release/bundle/constitutional-release-receipt.json',
];

describe('release pipeline', () => {
  it('reproduces a release bundle in isolation without mutating committed release artifacts', () => {
    const manifest = readReleaseManifest();
    const committedBefore = new Map(
      COMMITTED_RELEASE_FILES.filter((filePath) => existsSync(filePath)).map((filePath) => [filePath, sha256(filePath)]),
    );

    const workDir = mkdtempSync(path.join(tmpdir(), 'release-pipeline-'));
    copyFileSync('release/release-manifest.json', path.join(workDir, 'release-manifest.json'));
    const env = { ...process.env, AAES_RELEASE_DIR: workDir };

    const buildOutput = execFileSync('node', ['release/build-release.ts'], { encoding: 'utf8', env });
    const packageOutput = execFileSync('node', ['release/package-release.ts'], { encoding: 'utf8', env });
    const signOutput = execFileSync('node', ['release/sign-release.ts'], { encoding: 'utf8', env });
    const verifyOutput = execFileSync('node', ['release/verify-release.ts'], { encoding: 'utf8', env });

    expect(buildOutput).not.toContain('scaffold');
    expect(packageOutput).not.toContain('scaffold');
    expect(signOutput).not.toContain('scaffold');
    expect(verifyOutput).not.toContain('scaffold');
    expect(verifyOutput).toContain('release verified');
    expect(existsSync(path.join(workDir, 'checksums.json'))).toBe(true);
    expect(existsSync(path.join(workDir, 'signature.json'))).toBe(true);
    expect(existsSync(path.join(workDir, 'bundle/release-package.json'))).toBe(true);
    expect(existsSync(path.join(workDir, 'bundle/signature.json'))).toBe(true);
    expect(manifest.artifacts).toEqual(
        expect.arrayContaining([
          'docs/crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md',
          'docs/crk1/release/CIS_CONFORMANCE_SUITE_SPECIFICATION.md',
          'docs/crk1/release/CIS_CONFORMANCE_SUITE_INPUT.spec.json',
          'docs/crk1/release/CORI_ALPHA_PROOF_CHAIN.md',
          'docs/crk1/release/CORI_ALPHA_PROOF_CHAIN_FREEZE.md',
          'docs/crk1/release/CORI_ALPHA_MILESTONE_NOTE.md',
          'docs/crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_PROOF_PLAN.md',
          'docs/crk1/release/CORI_ALPHA_STATUS.schema.json',
          'docs/crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_STATUS.spec.json',
          'docs/crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_DASHBOARD.md',
        ]),
      );
    expect(existsSync(path.join(workDir, 'bundle/artifacts/docs/crk1/release/CORI_ALPHA_PROOF_CHAIN.md'))).toBe(true);
    expect(existsSync(path.join(workDir, 'bundle/artifacts/docs/crk1/release/CORI_ALPHA_PROOF_CHAIN_FREEZE.md'))).toBe(true);
    expect(existsSync(path.join(workDir, 'bundle/artifacts/docs/crk1/release/CORI_ALPHA_MILESTONE_NOTE.md'))).toBe(true);
    expect(existsSync(path.join(workDir, 'bundle/artifacts/docs/crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_PROOF_PLAN.md'))).toBe(true);
    expect(existsSync(path.join(workDir, 'bundle/artifacts/docs/crk1/release/CORI_ALPHA_STATUS.schema.json'))).toBe(true);
    expect(existsSync(path.join(workDir, 'bundle/artifacts/docs/crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_STATUS.spec.json'))).toBe(true);
    expect(existsSync(path.join(workDir, 'bundle/artifacts/docs/crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_DASHBOARD.md'))).toBe(true);
    expect(existsSync(path.join(workDir, 'bundle/artifacts/docs/crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md'))).toBe(true);

    for (const [filePath, hash] of committedBefore) {
      expect(sha256(filePath)).toBe(hash);
    }
  }, 30000);
});
