import { createHash } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { syncScorecardSnapshot } from '../../release/scorecard-sync.ts';

function sha256(filePath: string): string {
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

function snapshotBundleHashes(): Map<string, string> {
  const bundleRoot = path.join(process.cwd(), 'release', 'bundle');
  if (!existsSync(bundleRoot)) {
    return new Map();
  }
  const hashes = new Map<string, string>();
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const entryPath = path.join(dir, entry.name);
      const stats = statSync(entryPath);
      if (stats.isDirectory()) {
        walk(entryPath);
      } else if (stats.isFile()) {
        hashes.set(path.relative(process.cwd(), entryPath), sha256(entryPath));
      }
    }
  };
  walk(bundleRoot);
  return hashes;
}

const SOT_FILES = ['README.md', 'docs/scorecards/project-infi.md', 'docs-site/docs/overview.md'];
const ARTIFACT_SOT_FILES = ['README.md', 'docs/scorecards/project-infi.md'];

describe('scorecard-sync bundle integrity', () => {
  it('never mutates content-addressed release/bundle artifacts', () => {
    const before = snapshotBundleHashes();
    const repoRoot = tmpSyncRoot();

    for (const filePath of SOT_FILES) {
      const sourcePath = path.join(process.cwd(), filePath);
      const targetPath = path.join(repoRoot, filePath);
      if (existsSync(sourcePath)) {
        mkdirSync(path.dirname(targetPath), { recursive: true });
        copyFileSync(sourcePath, targetPath);
      }
    }

    const receipt = {
      constitutionalMaturity: 'Verified Prototype',
      proofSurfaceLevel: 'P2',
      commercialReadiness: 'Builder tier',
      receiptHash: 'test-receipt-hash',
      verificationDate: '2026-08-02T00:00:00.000Z',
    };

    syncScorecardSnapshot(receipt, { repoRoot });

    const overviewPath = path.join(repoRoot, 'docs-site/docs/overview.md');
    if (existsSync(overviewPath)) {
      expect(readFileSync(overviewPath, 'utf8')).toContain('test-receipt-hash');
    }

    for (const filePath of ARTIFACT_SOT_FILES) {
      const targetPath = path.join(repoRoot, filePath);
      if (existsSync(targetPath)) {
        const content = readFileSync(targetPath, 'utf8');
        expect(content).not.toContain('test-receipt-hash');
        expect(content).toContain('See `release/constitutional-release-receipt.json`');
      }
    }

    const after = snapshotBundleHashes();
    expect(after.size).toBe(before.size);
    for (const [filePath, hash] of before) {
      expect(after.get(filePath)).toBe(hash);
    }
  });
});

function tmpSyncRoot(): string {
  const root = path.join(tmpdir(), `scorecard-sync-${Date.now()}`);
  mkdirSync(root, { recursive: true });
  return root;
}
