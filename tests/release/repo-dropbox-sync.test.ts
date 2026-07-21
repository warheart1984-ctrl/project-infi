import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { describe, expect, it, vi } from 'vitest';

import {
  collectRepoDropboxChangeSummary,
  isMajorRepoChange,
  runRepoDropboxSync,
} from '../../release/repo-dropbox-sync.ts';

function initGitRepo(root: string): void {
  execFileSync('git', ['init'], { cwd: root, stdio: 'ignore' });
  execFileSync('git', ['config', 'user.email', 'codex@example.com'], { cwd: root, stdio: 'ignore' });
  execFileSync('git', ['config', 'user.name', 'Codex'], { cwd: root, stdio: 'ignore' });
}

function commitAll(root: string, message: string): string {
  execFileSync('git', ['add', '.'], { cwd: root, stdio: 'ignore' });
  execFileSync('git', ['commit', '-m', message], { cwd: root, stdio: 'ignore' });
  return execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim();
}

describe('repo Dropbox sync', () => {
  it('classifies major repo changes using the governed workspace surfaces', () => {
    expect(isMajorRepoChange('packages/foo/src/index.ts')).toBe(true);
    expect(isMajorRepoChange('services/api/src/server.ts')).toBe(true);
    expect(isMajorRepoChange('docs/README.md')).toBe(true);
    expect(isMajorRepoChange('package.json')).toBe(true);
    expect(isMajorRepoChange('scratch/notes.txt')).toBe(false);
  });

  it('creates a zip snapshot and manifest for major commits', async () => {
    const repoRoot = mkdtempSync(join(tmpdir(), 'repo-dropbox-sync-repo-'));
    const outputRoot = mkdtempSync(join(tmpdir(), 'repo-dropbox-sync-out-'));

    mkdirSync(join(repoRoot, 'packages', 'sample', 'src'), { recursive: true });
    writeFileSync(join(repoRoot, 'package.json'), JSON.stringify({ name: 'sample', private: true }, null, 2));
    writeFileSync(join(repoRoot, 'packages', 'sample', 'src', 'index.ts'), 'export const value = 42;\n');
    writeFileSync(join(repoRoot, 'scratch.txt'), 'minor change\n');

    initGitRepo(repoRoot);
    const commit = commitAll(repoRoot, 'feat: add sample package');

    const summary = collectRepoDropboxChangeSummary(repoRoot, commit);
    expect(summary.majorChange).toBe(true);
    expect(summary.majorChangeCount).toBe(2);
    expect(summary.changedFiles.map((entry) => entry.path)).toEqual(
      expect.arrayContaining([
        'package.json',
        'packages/sample/src/index.ts',
        'scratch.txt',
      ]),
    );

    const result = await runRepoDropboxSync({
      repoPath: repoRoot,
      commit,
      publishToDropbox: false,
      outputDir: outputRoot,
      dropboxRoot: '/team',
    });

    expect(result.status).toBe('skipped');
    expect(result.majorChange).toBe(true);
    expect(result.manifest.commit).toBe(commit);
    expect(result.manifest.snapshotKind).toBe('commit');
    expect(result.manifest.workingTreeDirty).toBe(false);
    expect(result.manifest.majorChange).toBe(true);
    expect(result.manifest.majorChangeCount).toBe(2);
    expect(result.manifest.changeCount).toBe(3);
    expect(result.manifest.dropboxPaths.archive).toContain(`/team/repo-snapshots/${result.manifest.repository}/history/`);
    expect(result.manifest.dropboxPaths.archive).toContain('/repo.zip');
    expect(existsSync(result.archivePath)).toBe(true);
    expect(existsSync(result.manifestPath)).toBe(true);
    expect(result.dropbox.transfers).toHaveLength(0);

    const manifest = JSON.parse(readFileSync(result.manifestPath, 'utf8')) as {
      commit: string;
      archive: { path: string; size: number; hash: string };
      majorChange: boolean;
      changedFiles: Array<{ path: string; major: boolean }>;
    };

    expect(manifest.commit).toBe(commit);
    expect(manifest.snapshotKind).toBe('commit');
    expect(manifest.majorChange).toBe(true);
    expect(manifest.changedFiles.filter((entry) => entry.major)).toHaveLength(2);
    expect(manifest.archive.size).toBeGreaterThan(0);
    expect(manifest.archive.hash).toHaveLength(64);
  }, 30000);

  it('captures dirty working-tree snapshots for live edits', async () => {
    const repoRoot = mkdtempSync(join(tmpdir(), 'repo-dropbox-sync-working-tree-'));
    const outputRoot = mkdtempSync(join(tmpdir(), 'repo-dropbox-sync-working-tree-out-'));

    mkdirSync(join(repoRoot, 'packages', 'sample', 'src'), { recursive: true });
    writeFileSync(join(repoRoot, 'package.json'), JSON.stringify({ name: 'sample', private: true }, null, 2));
    writeFileSync(join(repoRoot, 'packages', 'sample', 'src', 'index.ts'), 'export const value = 1;\n');

    initGitRepo(repoRoot);
    commitAll(repoRoot, 'feat: seed sample package');

    writeFileSync(join(repoRoot, 'packages', 'sample', 'src', 'index.ts'), 'export const value = 2;\n');
    writeFileSync(join(repoRoot, 'scratch.txt'), 'dirty working tree change\n');

    const result = await runRepoDropboxSync({
      repoPath: repoRoot,
      publishToDropbox: false,
      outputDir: outputRoot,
      dropboxRoot: '/team',
      snapshotMode: 'working-tree',
    });

    expect(result.status).toBe('skipped');
    expect(result.manifest.snapshotKind).toBe('working-tree');
    expect(result.manifest.workingTreeDirty).toBe(true);
    expect(result.manifest.majorChange).toBe(true);
    expect(result.manifest.changedFiles.some((entry) => entry.path === 'scratch.txt')).toBe(true);
    expect(existsSync(result.archivePath)).toBe(true);
    expect(existsSync(result.manifestPath)).toBe(true);
    expect(result.manifest.dropboxPaths.archive).toContain(`/team/repo-snapshots/${result.manifest.repository}/history/`);
    expect(result.manifest.dropboxPaths.archive).toContain('/repo.zip');
    expect(result.dropbox.retention.status).toBe('skipped');
  }, 30000);

  it('falls back to the Dropbox sync folder when API upload is unavailable', async () => {
    const repoRoot = mkdtempSync(join(tmpdir(), 'repo-dropbox-sync-fallback-repo-'));
    const outputRoot = mkdtempSync(join(tmpdir(), 'repo-dropbox-sync-fallback-out-'));
    const syncFolderRoot = mkdtempSync(join(tmpdir(), 'repo-dropbox-sync-fallback-folder-'));

    mkdirSync(join(repoRoot, 'packages', 'sample', 'src'), { recursive: true });
    writeFileSync(join(repoRoot, 'package.json'), JSON.stringify({ name: 'sample', private: true }, null, 2));
    writeFileSync(join(repoRoot, 'packages', 'sample', 'src', 'index.ts'), 'export const value = 7;\n');

    initGitRepo(repoRoot);
    const commit = commitAll(repoRoot, 'feat: seed sample package');

    const originalToken = process.env.DROPBOX_TOKEN;
    process.env.DROPBOX_TOKEN = 'token';
    const originalFetch = globalThis.fetch;
    vi.stubGlobal('fetch', async () => ({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      text: async () => 'unauthorized',
    }) as Response);

    try {
      const result = await runRepoDropboxSync({
        repoPath: repoRoot,
        commit,
        publishToDropbox: true,
        outputDir: outputRoot,
        dropboxRoot: '/team',
        syncFolderRoot,
      });

      expect(result.status).toBe('uploaded');
      expect(result.dropbox.backend).toBe('folder');
      expect(result.dropbox.syncFolderRoot).toBe(syncFolderRoot);
      expect(existsSync(join(syncFolderRoot, 'repo-snapshots', result.manifest.repository, 'history', result.manifest.snapshotId, 'repo.zip'))).toBe(true);
      expect(existsSync(join(syncFolderRoot, 'repo-snapshots', result.manifest.repository, 'history', result.manifest.snapshotId, 'repo.json'))).toBe(true);
      expect(existsSync(join(syncFolderRoot, 'repo-snapshots', result.manifest.repository, 'latest', 'repo-snapshot.zip'))).toBe(true);
      expect(existsSync(join(syncFolderRoot, 'repo-snapshots', result.manifest.repository, 'latest', 'repo-snapshot.json'))).toBe(true);
      expect(result.dropbox.transfers.every((transfer) => transfer.backend === 'folder')).toBe(true);
    } finally {
      if (originalToken === undefined) {
        delete process.env.DROPBOX_TOKEN;
      } else {
        process.env.DROPBOX_TOKEN = originalToken;
      }
      globalThis.fetch = originalFetch;
      vi.unstubAllGlobals();
    }
  }, 30000);
});
