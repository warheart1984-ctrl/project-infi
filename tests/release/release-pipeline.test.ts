import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';

function readReleaseManifest(): { artifacts?: string[] } {
  return JSON.parse(readFileSync(path.join(process.cwd(), 'release', 'release-manifest.json'), 'utf8')) as {
    artifacts?: string[];
  };
}

describe('release pipeline', () => {
  it('packages and verifies a real release bundle', () => {
    const manifest = readReleaseManifest();
    const buildOutput = execFileSync('node', ['release/build-release.ts'], { encoding: 'utf8' });
    const packageOutput = execFileSync('node', ['release/package-release.ts'], { encoding: 'utf8' });
    const signOutput = execFileSync('node', ['release/sign-release.ts'], { encoding: 'utf8' });
    const verifyOutput = execFileSync('node', ['release/verify-release.ts'], { encoding: 'utf8' });

    expect(buildOutput).not.toContain('scaffold');
    expect(packageOutput).not.toContain('scaffold');
    expect(signOutput).not.toContain('scaffold');
    expect(verifyOutput).not.toContain('scaffold');
    expect(verifyOutput).toContain('release verified');
    expect(existsSync('release/checksums.json')).toBe(true);
    expect(existsSync('release/signature.json')).toBe(true);
    expect(existsSync('release/bundle/release-package.json')).toBe(true);
    expect(existsSync('release/bundle/signature.json')).toBe(true);
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
    expect(existsSync('release/bundle/artifacts/docs/crk1/release/CORI_ALPHA_PROOF_CHAIN.md')).toBe(true);
    expect(existsSync('release/bundle/artifacts/docs/crk1/release/CORI_ALPHA_PROOF_CHAIN_FREEZE.md')).toBe(true);
    expect(existsSync('release/bundle/artifacts/docs/crk1/release/CORI_ALPHA_MILESTONE_NOTE.md')).toBe(true);
    expect(existsSync('release/bundle/artifacts/docs/crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_PROOF_PLAN.md')).toBe(true);
    expect(existsSync('release/bundle/artifacts/docs/crk1/release/CORI_ALPHA_STATUS.schema.json')).toBe(true);
    expect(existsSync('release/bundle/artifacts/docs/crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_STATUS.spec.json')).toBe(true);
    expect(existsSync('release/bundle/artifacts/docs/crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_DASHBOARD.md')).toBe(true);
    expect(existsSync('release/bundle/artifacts/docs/crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md')).toBe(true);
  }, 30000);
});
