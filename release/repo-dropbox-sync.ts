import { createHash } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { execFileSync, spawnSync } from 'node:child_process';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export type RepoDropboxChangeKind = 'added' | 'copied' | 'deleted' | 'modified' | 'renamed' | 'type_changed' | 'untracked' | 'unknown';
export type RepoDropboxSyncStatus = 'uploaded' | 'skipped' | 'failed';
export type RepoDropboxSnapshotKind = 'commit' | 'working-tree';
export type RepoDropboxSnapshotMode = RepoDropboxSnapshotKind | 'auto';

export interface RepoDropboxSyncInput {
  repoPath?: string;
  repo_path?: string;
  commit?: string;
  branch?: string | null;
  branch_name?: string | null;
  developerId?: string;
  developer_id?: string;
  dropboxRoot?: string;
  dropbox_root?: string;
  syncFolderRoot?: string;
  sync_folder_root?: string;
  publishToDropbox?: boolean;
  snapshotMode?: RepoDropboxSnapshotMode;
  snapshot_mode?: RepoDropboxSnapshotMode;
  outputDir?: string;
  output_dir?: string;
  historyLimit?: number;
  history_limit?: number;
}

export interface RepoDropboxChangeEntry {
  status: RepoDropboxChangeKind;
  path: string;
  previousPath?: string;
  major: boolean;
}

export interface RepoDropboxArchiveRef {
  path: string;
  hash: string;
  size: number;
}

export interface RepoDropboxTransfer {
  localPath: string;
  remotePath: string;
  status: RepoDropboxSyncStatus;
  backend: 'api' | 'folder';
  error?: string;
}

export interface RepoDropboxSyncManifest {
  schemaVersion: '1.0';
  repository: string;
  repoPath: string;
  commit: string;
  parentCommit: string | null;
  branch: string | null;
  developerId: string;
  createdAt: string;
  snapshotId: string;
  snapshotKind: RepoDropboxSnapshotKind;
  workingTreeDirty: boolean;
  majorChange: boolean;
  changeCount: number;
  majorChangeCount: number;
  changedFiles: RepoDropboxChangeEntry[];
  archive: RepoDropboxArchiveRef;
  dropboxRoot: string;
  syncFolderRoot: string | null;
  dropboxPaths: {
    archive: string;
    manifest: string;
    latestArchive: string;
    latestManifest: string;
    snapshotFolder: string;
    latestFolder: string;
    historyFolder: string;
  };
}

export interface RepoDropboxSyncResult {
  status: RepoDropboxSyncStatus;
  reason: string;
  majorChange: boolean;
  manifestPath: string;
  archivePath: string;
  manifest: RepoDropboxSyncManifest;
  dropbox: {
    enabled: boolean;
    root: string;
    syncFolderRoot: string | null;
    backend: 'api' | 'folder' | 'none';
    retentionHistoryLimit: number;
    transfers: RepoDropboxTransfer[];
    retention: RepoDropboxRetentionResult;
  };
}

export interface RepoDropboxRetentionResult {
  status: 'skipped' | 'applied' | 'failed';
  historyLimit: number;
  removedFolders: string[];
  errors: string[];
}

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const ignoredTopLevelRoots = new Set([
  '.git',
  '.local',
  '.next',
  '.pytest_cache',
  '.runtime',
  '.tmp',
  '.venv',
  '.venv-test',
  '__pycache__',
  'build',
  'ci-artifacts',
  'coverage',
  'dist',
  'node_modules',
  'temp',
  'tmp',
]);
const majorRootFiles = new Set([
  'package.json',
  'pnpm-lock.yaml',
  'pnpm-workspace.yaml',
  'tsconfig.json',
  'tsconfig.base.json',
  'eslint.config.mjs',
  'vitest.config.ts',
  'docker-compose.yml',
  '.npmrc',
]);

function discoverMajorRootPrefixes(): string[] {
  return readdirSync(repoRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .filter((name) => !ignoredTopLevelRoots.has(name))
    .map((name) => `${name}/`);
}

const majorRootPrefixes = discoverMajorRootPrefixes();

function currentTimestamp(): string {
  return new Date().toISOString();
}

function git(repoPath: string, args: string[]): string {
  return execFileSync('git', ['-C', repoPath, ...args], { encoding: 'utf8' }).trim();
}

function gitOptional(repoPath: string, args: string[]): string | null {
  const result = spawnSync('git', ['-C', repoPath, ...args], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  });

  if (result.status !== 0 || typeof result.stdout !== 'string') {
    return null;
  }

  const output = result.stdout.trim();
  return output.length > 0 ? output : null;
}

function gitOptionalRaw(repoPath: string, args: string[]): string | null {
  const result = spawnSync('git', ['-C', repoPath, ...args], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  });

  if (result.status !== 0 || typeof result.stdout !== 'string') {
    return null;
  }

  return result.stdout.length > 0 ? result.stdout : null;
}

function normalizePath(value: string): string {
  return value.replace(/\\/g, '/').replace(/^\.\/+/, '').replace(/^\/+/, '').replace(/\/+$/, '');
}

function normalizeDropboxRoot(value: string): string {
  const normalized = value.replace(/\\/g, '/').replace(/\/+$/, '');
  if (normalized.startsWith('/')) {
    return normalized;
  }
  return `/${normalized.replace(/^\/+/, '')}`;
}

function hashBuffer(buffer: Buffer | string): string {
  return createHash('sha256').update(buffer).digest('hex');
}

function ensureDir(path: string): void {
  mkdirSync(path, { recursive: true });
}

function writeJson(filePath: string, value: unknown): void {
  ensureDir(dirname(filePath));
  writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function readFileHash(filePath: string): string {
  return hashBuffer(readFileSync(filePath));
}

function resolveRepoPath(input: RepoDropboxSyncInput): string {
  const repoPath = input.repoPath ?? input.repo_path ?? repoRoot;
  return resolve(repoPath);
}

function resolveDeveloperId(input: RepoDropboxSyncInput): string {
  return input.developerId ?? input.developer_id ?? process.env.GIT_AUTHOR_NAME ?? process.env.USER ?? 'unknown';
}

function resolveBranch(input: RepoDropboxSyncInput, repoPath: string): string | null {
  if (typeof input.branch === 'string') {
    return input.branch;
  }
  if (typeof input.branch_name === 'string') {
    return input.branch_name;
  }
  return gitOptional(repoPath, ['rev-parse', '--abbrev-ref', 'HEAD']);
}

function resolveDropboxRoot(input: RepoDropboxSyncInput): string {
  const value = input.dropboxRoot ?? input.dropbox_root ?? process.env.REPO_DROPBOX_ROOT ?? process.env.DROPBOX_REPO_ROOT ?? '/team/project-infi';
  return normalizeDropboxRoot(value);
}

function resolveDropboxSyncFolderRoot(input: RepoDropboxSyncInput): string | null {
  const value = input.syncFolderRoot
    ?? input.sync_folder_root
    ?? process.env.REPO_DROPBOX_SYNC_FOLDER_ROOT
    ?? process.env.DROPBOX_SYNC_FOLDER_ROOT
    ?? process.env.DROPBOX_FOLDER_ROOT
    ?? process.env.DROPBOX_LOCAL_SYNC_FOLDER_ROOT;
  if (!value || value.trim().length === 0) {
    return null;
  }
  return resolve(value.trim());
}

function resolveOutputDir(input: RepoDropboxSyncInput): { path: string; shouldCleanup: boolean } {
  const explicit = input.outputDir ?? input.output_dir;
  if (explicit && explicit.trim().length > 0) {
    return { path: resolve(explicit), shouldCleanup: false };
  }
  return { path: mkdtempSync(join(tmpdir(), 'repo-dropbox-sync-')), shouldCleanup: true };
}

function resolveHistoryLimit(input: RepoDropboxSyncInput): number {
  const value = input.historyLimit ?? input.history_limit ?? Number(process.env.REPO_DROPBOX_HISTORY_LIMIT ?? '5');
  if (!Number.isFinite(value) || value < 0) {
    return 5;
  }
  return Math.floor(value);
}

function resolveSnapshotMode(input: RepoDropboxSyncInput): RepoDropboxSnapshotMode {
  return input.snapshotMode ?? input.snapshot_mode ?? (process.env.REPO_DROPBOX_SNAPSHOT_MODE as RepoDropboxSnapshotMode | undefined) ?? 'auto';
}

function parseChangedFiles(repoPath: string, commit: string): RepoDropboxChangeEntry[] {
  const raw = gitOptional(repoPath, ['show', '--pretty=format:', '--name-status', commit]) ?? '';
  const entries: RepoDropboxChangeEntry[] = [];

  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed) {
      continue;
    }

    const parts = trimmed.split('\t').filter(Boolean);
    if (parts.length === 0) {
      continue;
    }

    const status = parts[0] ?? 'M';
    const kind = normalizeChangeKind(status);
    if (status.startsWith('R') || status.startsWith('C')) {
      const previousPath = parts[1] ? normalizePath(parts[1]) : undefined;
      const path = parts[2] ? normalizePath(parts[2]) : previousPath ?? '';
      if (path.length === 0) {
        continue;
      }
      entries.push({
        status: kind,
        path,
        previousPath,
        major: isMajorRepoChange(path) || (previousPath ? isMajorRepoChange(previousPath) : false),
      });
      continue;
    }

    const path = parts[1] ? normalizePath(parts[1]) : '';
    if (path.length === 0) {
      continue;
    }

    entries.push({
      status: kind,
      path,
      major: isMajorRepoChange(path),
    });
  }

  return dedupeChangeEntries(entries);
}

function isWorkingTreeDirty(repoPath: string): boolean {
  const raw = gitOptionalRaw(repoPath, ['status', '--porcelain=v1', '--untracked-files=all']) ?? '';
  return raw.trim().length > 0;
}

function parseWorkingTreeChanges(repoPath: string): RepoDropboxChangeEntry[] {
  const raw = gitOptionalRaw(repoPath, ['status', '--porcelain=v1', '--untracked-files=all']) ?? '';
  const entries: RepoDropboxChangeEntry[] = [];

  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trimEnd();
    if (!trimmed) {
      continue;
    }

    const match = /^(.{2})\s+(.*)$/.exec(trimmed);
    if (!match) {
      continue;
    }

    const statusCode = match[1] ?? '';
    const payload = match[2] ?? '';
    if (statusCode === '??') {
      const path = normalizePath(payload);
      if (path.length > 0) {
        entries.push({ status: 'untracked', path, major: isMajorRepoChange(path) });
      }
      continue;
    }

    const normalizedStatus = statusCode.trim().length > 0 ? statusCode.trim()[0] ?? 'M' : 'M';
    const kind = normalizeChangeKind(normalizedStatus);
    if (statusCode.startsWith('R') || statusCode.startsWith('C')) {
      const [previous, next] = payload.split('\t');
      const previousPath = previous ? normalizePath(previous) : undefined;
      const path = next ? normalizePath(next) : previousPath ?? '';
      if (path.length > 0) {
        entries.push({
          status: kind,
          path,
          previousPath,
          major: isMajorRepoChange(path) || (previousPath ? isMajorRepoChange(previousPath) : false),
        });
      }
      continue;
    }

    const path = normalizePath(payload);
    if (path.length > 0) {
      entries.push({ status: kind, path, major: isMajorRepoChange(path) });
    }
  }

  return dedupeChangeEntries(entries);
}

function formatUtcStamp(value: string): string {
  const date = new Date(value);
  const year = String(date.getUTCFullYear()).padStart(4, '0');
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  const hour = String(date.getUTCHours()).padStart(2, '0');
  const minute = String(date.getUTCMinutes()).padStart(2, '0');
  const second = String(date.getUTCSeconds()).padStart(2, '0');
  return `${year}${month}${day}T${hour}${minute}${second}Z`;
}

function createSnapshotId(snapshotKind: RepoDropboxSnapshotKind, commit: string, createdAt: string): string {
  const stamp = formatUtcStamp(createdAt);
  const shortCommit = commit.slice(0, 12);
  return `${stamp}-${snapshotKind}-${shortCommit}`;
}

function summarizeChanges(changedFiles: RepoDropboxChangeEntry[]): {
  changedFiles: RepoDropboxChangeEntry[];
  majorChange: boolean;
  majorChangeCount: number;
} {
  const majorChangeCount = changedFiles.filter((entry) => entry.major).length;
  return {
    changedFiles,
    majorChange: majorChangeCount > 0,
    majorChangeCount,
  };
}

function getWorkingTreeFiles(repoPath: string): string[] {
  const raw = gitOptional(repoPath, ['ls-files', '-co', '--exclude-standard', '--full-name']) ?? '';
  const entries = new Set<string>();
  for (const line of raw.split(/\r?\n/)) {
    const normalized = normalizePath(line.trim());
    if (normalized.length === 0) {
      continue;
    }
    if (normalized === '.git' || normalized.startsWith('.git/')) {
      continue;
    }
    entries.add(normalized);
  }
  return [...entries].sort();
}

function stageWorkingTreeSnapshot(repoPath: string, stageDir: string): void {
  const files = getWorkingTreeFiles(repoPath);
  for (const relativePath of files) {
    const sourcePath = resolve(repoPath, relativePath);
    if (!existsSync(sourcePath)) {
      continue;
    }
    const stats = statSync(sourcePath);
    if (!stats.isFile()) {
      continue;
    }
    const destinationPath = resolve(stageDir, relativePath);
    mkdirSync(dirname(destinationPath), { recursive: true });
    copyFileSync(sourcePath, destinationPath);
  }
}

function psQuote(value: string): string {
  return `'${value.replace(/'/g, "''")}'`;
}

function createZipFromDirectory(sourceDir: string, archivePath: string): void {
  ensureDir(dirname(archivePath));
  const script = [
    'Add-Type -AssemblyName System.IO.Compression.FileSystem;',
    `[System.IO.Compression.ZipFile]::CreateFromDirectory(${psQuote(sourceDir)}, ${psQuote(archivePath)}, [System.IO.Compression.CompressionLevel]::Optimal, $false)`,
  ].join(' ');
  execFileSync('powershell', ['-NoProfile', '-Command', script], { stdio: 'pipe' });
}

function createRepoSnapshotArchive(repoPath: string, snapshotKind: RepoDropboxSnapshotKind, commit: string, archivePath: string): void {
  if (snapshotKind === 'commit') {
    execFileSync('git', ['-C', repoPath, 'archive', '--format=zip', '--output', archivePath, commit], { stdio: 'pipe' });
    return;
  }

  const stageDir = mkdtempSync(join(tmpdir(), 'repo-dropbox-stage-'));
  try {
    stageWorkingTreeSnapshot(repoPath, stageDir);
    createZipFromDirectory(stageDir, archivePath);
  } finally {
    rmSync(stageDir, { recursive: true, force: true });
  }
}

function dedupeChangeEntries(entries: RepoDropboxChangeEntry[]): RepoDropboxChangeEntry[] {
  const seen = new Set<string>();
  const result: RepoDropboxChangeEntry[] = [];
  for (const entry of entries) {
    const key = `${entry.status}:${entry.path}:${entry.previousPath ?? ''}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    result.push(entry);
  }
  return result;
}

function normalizeChangeKind(status: string): RepoDropboxChangeKind {
  if (status === 'A') {
    return 'added';
  }
  if (status === 'M') {
    return 'modified';
  }
  if (status === 'D') {
    return 'deleted';
  }
  if (status.startsWith('R')) {
    return 'renamed';
  }
  if (status.startsWith('C')) {
    return 'copied';
  }
  if (status === 'T') {
    return 'type_changed';
  }
  return 'unknown';
}

export function isMajorRepoChange(path: string): boolean {
  const normalized = normalizePath(path);
  if (normalized.length === 0) {
    return false;
  }

  if (majorRootFiles.has(normalized)) {
    return true;
  }

  return majorRootPrefixes.some((prefix) => normalized === prefix.slice(0, -1) || normalized.startsWith(prefix));
}

export function getRepoDropboxRepositoryName(repoPath: string): string {
  return normalizePath(resolve(repoPath).split(/[\\/]/).at(-1) ?? 'repo') || 'repo';
}

export function collectRepoDropboxChangeSummary(repoPath: string, commit?: string): {
  commit: string;
  parentCommit: string | null;
  branch: string | null;
  developerId: string;
  repository: string;
  changedFiles: RepoDropboxChangeEntry[];
  majorChange: boolean;
  majorChangeCount: number;
} {
  const resolvedRepoPath = resolve(repoPath);
  if (!existsSync(resolvedRepoPath)) {
    throw new Error(`repository path does not exist: ${resolvedRepoPath}`);
  }

  const resolvedCommit = commit ?? git(resolvedRepoPath, ['rev-parse', 'HEAD']);
  const parentCommit = gitOptional(resolvedRepoPath, ['rev-parse', `${resolvedCommit}^`]);
  const branch = gitOptional(resolvedRepoPath, ['rev-parse', '--abbrev-ref', 'HEAD']);
  const developerId = resolveDeveloperId({});
  const repository = getRepoDropboxRepositoryName(resolvedRepoPath);
  const changedFiles = parseChangedFiles(resolvedRepoPath, resolvedCommit);
  const { majorChange, majorChangeCount } = summarizeChanges(changedFiles);

  return {
    commit: resolvedCommit,
    parentCommit,
    branch,
    developerId,
    repository,
    changedFiles,
    majorChange,
    majorChangeCount,
  };
}

export function collectRepoDropboxWorkingTreeSummary(repoPath: string): {
  changedFiles: RepoDropboxChangeEntry[];
  majorChange: boolean;
  majorChangeCount: number;
} {
  const resolvedRepoPath = resolve(repoPath);
  if (!existsSync(resolvedRepoPath)) {
    throw new Error(`repository path does not exist: ${resolvedRepoPath}`);
  }

  return summarizeChanges(parseWorkingTreeChanges(resolvedRepoPath));
}

async function uploadFileToDropbox(localPath: string, remotePath: string): Promise<void> {
  const token = process.env.DROPBOX_TOKEN;
  if (!token) {
    return;
  }

  const response = await fetch('https://content.dropboxapi.com/2/files/upload', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Dropbox-API-Arg': JSON.stringify({
        path: remotePath,
        mode: 'overwrite',
        mute: true,
        autorename: false,
      }),
      'Content-Type': 'application/octet-stream',
    },
    body: readFileSync(localPath),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Dropbox upload failed for ${remotePath}: ${response.status} ${response.statusText}${body ? ` - ${body}` : ''}`);
  }
}

async function copyFileToDropboxFolder(localPath: string, folderRoot: string, remotePath: string): Promise<void> {
  void folderRoot;
  const targetPath = resolve(remotePath);
  ensureDir(dirname(targetPath));
  copyFileSync(localPath, targetPath);
}

async function callDropboxApi<T>(endpoint: string, payload: unknown): Promise<T> {
  const token = process.env.DROPBOX_TOKEN;
  if (!token) {
    throw new Error('Dropbox token is missing');
  }

  const response = await fetch(`https://api.dropboxapi.com/2/${endpoint}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Dropbox API ${endpoint} failed: ${response.status} ${response.statusText}${body ? ` - ${body}` : ''}`);
  }

  return response.json() as Promise<T>;
}

function buildDropboxPaths(dropboxRoot: string, repository: string, snapshotId: string): RepoDropboxSyncManifest['dropboxPaths'] {
  const remoteRoot = `${dropboxRoot}/repo-snapshots/${repository}`;
  const snapshotFolder = `${remoteRoot}/history/${snapshotId}`;
  return {
    archive: `${snapshotFolder}/repo.zip`,
    manifest: `${snapshotFolder}/repo.json`,
    latestArchive: `${remoteRoot}/latest/repo-snapshot.zip`,
    latestManifest: `${remoteRoot}/latest/repo-snapshot.json`,
    snapshotFolder,
    latestFolder: `${remoteRoot}/latest`,
    historyFolder: `${remoteRoot}/history`,
  };
}

function buildDropboxFolderPaths(folderRoot: string, repository: string, snapshotId: string): RepoDropboxSyncManifest['dropboxPaths'] {
  const remoteRoot = resolve(folderRoot, 'repo-snapshots', repository).replace(/\\/g, '/');
  const snapshotFolder = `${remoteRoot}/history/${snapshotId}`;
  return {
    archive: `${snapshotFolder}/repo.zip`,
    manifest: `${snapshotFolder}/repo.json`,
    latestArchive: `${remoteRoot}/latest/repo-snapshot.zip`,
    latestManifest: `${remoteRoot}/latest/repo-snapshot.json`,
    snapshotFolder,
    latestFolder: `${remoteRoot}/latest`,
    historyFolder: `${remoteRoot}/history`,
  };
}

async function enforceDropboxRetention(
  root: string,
  repository: string,
  historyLimit: number,
): Promise<RepoDropboxRetentionResult> {
  if (historyLimit <= 0) {
    return {
      status: 'skipped',
      historyLimit,
      removedFolders: [],
      errors: [],
    };
  }

  const historyPath = `${root}/repo-snapshots/${repository}/history`;
  let response: {
    entries: Array<{ '.tag': string; path_display?: string; name?: string }>;
    cursor: string;
    has_more: boolean;
  };
  try {
    response = await callDropboxApi<{
      entries: Array<{ '.tag': string; path_display?: string; name?: string }>;
      cursor: string;
      has_more: boolean;
    }>('files/list_folder', {
      path: historyPath,
      recursive: false,
      include_deleted: false,
      include_has_explicit_shared_members: false,
      include_media_info: false,
      include_mounted_folders: false,
      include_non_downloadable_files: false,
      limit: 1000,
    });
  } catch (error) {
    return {
      status: 'skipped',
      historyLimit,
      removedFolders: [],
      errors: [error instanceof Error ? error.message : String(error)],
    };
  }

  const folders = response.entries
    .filter((entry) => entry['.tag'] === 'folder')
    .map((entry) => ({
      path: entry.path_display ?? `${historyPath}/${entry.name ?? ''}`,
      name: entry.name ?? basename(entry.path_display ?? ''),
    }))
    .filter((entry) => entry.path.length > historyPath.length + 1)
    .sort((left, right) => right.name.localeCompare(left.name));

  const removedFolders: string[] = [];
  const errors: string[] = [];

  for (const folder of folders.slice(historyLimit)) {
    try {
      await callDropboxApi('files/delete_v2', { path: folder.path });
      removedFolders.push(folder.path);
    } catch (error) {
      errors.push(error instanceof Error ? error.message : String(error));
    }
  }

  return {
    status: errors.length > 0 ? 'failed' : removedFolders.length > 0 ? 'applied' : 'skipped',
    historyLimit,
    removedFolders,
    errors,
  };
}

function enforceDropboxFolderRetention(
  folderRoot: string,
  repository: string,
  historyLimit: number,
): RepoDropboxRetentionResult {
  if (historyLimit <= 0) {
    return {
      status: 'skipped',
      historyLimit,
      removedFolders: [],
      errors: [],
    };
  }

  const historyPath = resolve(folderRoot, 'repo-snapshots', repository, 'history');
  if (!existsSync(historyPath)) {
    return {
      status: 'skipped',
      historyLimit,
      removedFolders: [],
      errors: [],
    };
  }

  const folders = readdirSync(historyPath, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort()
    .reverse();

  const removedFolders: string[] = [];
  const errors: string[] = [];

  for (const folder of folders.slice(historyLimit)) {
    const pathToRemove = resolve(historyPath, folder);
    try {
      rmSync(pathToRemove, { recursive: true, force: true });
      removedFolders.push(pathToRemove);
    } catch (error) {
      errors.push(error instanceof Error ? error.message : String(error));
    }
  }

  return {
    status: errors.length > 0 ? 'failed' : removedFolders.length > 0 ? 'applied' : 'skipped',
    historyLimit,
    removedFolders,
    errors,
  };
}

async function transferSnapshotViaDropboxApi(
  archivePath: string,
  manifestPath: string,
  dropboxPaths: RepoDropboxSyncManifest['dropboxPaths'],
): Promise<RepoDropboxTransfer[]> {
  const uploadTargets = [
    { localPath: archivePath, remotePath: dropboxPaths.archive },
    { localPath: manifestPath, remotePath: dropboxPaths.manifest },
    { localPath: archivePath, remotePath: dropboxPaths.latestArchive },
    { localPath: manifestPath, remotePath: dropboxPaths.latestManifest },
  ];

  const transfers: RepoDropboxTransfer[] = [];
  for (const target of uploadTargets) {
    try {
      await uploadFileToDropbox(target.localPath, target.remotePath);
      transfers.push({ ...target, status: 'uploaded', backend: 'api' });
    } catch (error) {
      transfers.push({
        ...target,
        status: 'failed',
        backend: 'api',
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  return transfers;
}

async function transferSnapshotViaDropboxFolder(
  archivePath: string,
  manifestPath: string,
  folderRoot: string,
  dropboxPaths: RepoDropboxSyncManifest['dropboxPaths'],
): Promise<RepoDropboxTransfer[]> {
  const uploadTargets = [
    { localPath: archivePath, remotePath: dropboxPaths.archive },
    { localPath: manifestPath, remotePath: dropboxPaths.manifest },
    { localPath: archivePath, remotePath: dropboxPaths.latestArchive },
    { localPath: manifestPath, remotePath: dropboxPaths.latestManifest },
  ];

  const transfers: RepoDropboxTransfer[] = [];
  for (const target of uploadTargets) {
    try {
      await copyFileToDropboxFolder(target.localPath, folderRoot, target.remotePath);
      transfers.push({ ...target, status: 'uploaded', backend: 'folder' });
    } catch (error) {
      transfers.push({
        ...target,
        status: 'failed',
        backend: 'folder',
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  return transfers;
}

export async function runRepoDropboxSync(input: RepoDropboxSyncInput = {}): Promise<RepoDropboxSyncResult> {
  const repoPath = resolveRepoPath(input);
  if (!existsSync(repoPath)) {
    throw new Error(`repository path does not exist: ${repoPath}`);
  }

  const commitSummary = collectRepoDropboxChangeSummary(repoPath, input.commit);
  const dropboxRoot = resolveDropboxRoot(input);
  const outputDir = resolveOutputDir(input);
  const repository = commitSummary.repository;
  const createdAt = currentTimestamp();
  const historyLimit = resolveHistoryLimit(input);
  const snapshotMode = resolveSnapshotMode(input);
  const syncFolderRoot = resolveDropboxSyncFolderRoot(input);
  const workingTreeDirty = isWorkingTreeDirty(repoPath);
  const snapshotKind: RepoDropboxSnapshotKind = snapshotMode === 'commit'
    ? 'commit'
    : snapshotMode === 'working-tree'
      ? 'working-tree'
      : workingTreeDirty
        ? 'working-tree'
        : 'commit';
  const snapshotSummary = snapshotKind === 'working-tree'
    ? collectRepoDropboxWorkingTreeSummary(repoPath)
    : {
        changedFiles: commitSummary.changedFiles,
        majorChange: commitSummary.majorChange,
        majorChangeCount: commitSummary.majorChangeCount,
      };
  const snapshotId = createSnapshotId(snapshotKind, commitSummary.commit, createdAt);
  const archivePath = resolve(outputDir.path, `${snapshotId}.zip`);
  const manifestPath = resolve(outputDir.path, `${snapshotId}.json`);
  const dropboxPaths = buildDropboxPaths(dropboxRoot, repository, snapshotId);
  const tokenPresent = Boolean(process.env.DROPBOX_TOKEN);
  const shouldPublish = input.publishToDropbox ?? (tokenPresent || Boolean(syncFolderRoot));

  ensureDir(outputDir.path);
  createRepoSnapshotArchive(repoPath, snapshotKind, commitSummary.commit, archivePath);

  const archive = {
    path: archivePath,
    hash: readFileHash(archivePath),
    size: existsSync(archivePath) ? statSync(archivePath).size : 0,
  };

  const manifest: RepoDropboxSyncManifest = {
    schemaVersion: '1.0',
    repository,
    repoPath,
    commit: commitSummary.commit,
    parentCommit: commitSummary.parentCommit,
    branch: commitSummary.branch ?? resolveBranch(input, repoPath),
    developerId: resolveDeveloperId(input),
    createdAt,
    snapshotId,
    snapshotKind,
    workingTreeDirty,
    majorChange: snapshotSummary.majorChange,
    changeCount: snapshotSummary.changedFiles.length,
    majorChangeCount: snapshotSummary.majorChangeCount,
    changedFiles: snapshotSummary.changedFiles,
    archive,
    dropboxRoot,
    dropboxPaths,
  };

  writeJson(manifestPath, manifest);

  const transfers: RepoDropboxTransfer[] = [];
  let transferBackend: 'api' | 'folder' | 'none' = 'none';
  let apiAttemptFailed = false;
  if (snapshotSummary.majorChange && shouldPublish) {
    if (tokenPresent) {
      transfers.push(...await transferSnapshotViaDropboxApi(archivePath, manifestPath, dropboxPaths));
      if (!transfers.some((transfer) => transfer.status === 'failed')) {
        transferBackend = 'api';
      } else {
        apiAttemptFailed = true;
      }
    }

    if (transferBackend !== 'api' && syncFolderRoot) {
      const folderTransfers = await transferSnapshotViaDropboxFolder(
        archivePath,
        manifestPath,
        syncFolderRoot,
        buildDropboxFolderPaths(syncFolderRoot, repository, snapshotId),
      );
      transfers.length = 0;
      transfers.push(...folderTransfers);
      transferBackend = 'folder';
    }
  }

  const retention = transferBackend === 'api' && snapshotSummary.majorChange
    ? await enforceDropboxRetention(dropboxRoot, repository, historyLimit)
    : transferBackend === 'folder' && snapshotSummary.majorChange && syncFolderRoot
      ? enforceDropboxFolderRetention(syncFolderRoot, repository, historyLimit)
    : {
        status: 'skipped' as const,
        historyLimit,
        removedFolders: [] as string[],
        errors: [] as string[],
      };

  const hasFailures = transfers.some((transfer) => transfer.status === 'failed');
  const retentionFailed = retention.status === 'failed';
  const result: RepoDropboxSyncResult = {
    status: hasFailures || retentionFailed ? 'failed' : snapshotSummary.majorChange && transferBackend !== 'none' ? 'uploaded' : 'skipped',
    reason: snapshotSummary.majorChange
      ? transferBackend === 'api'
        ? hasFailures && retentionFailed
          ? 'Dropbox API uploads and retention cleanup failed'
          : hasFailures
            ? 'one or more Dropbox API uploads failed'
            : retentionFailed
              ? 'Dropbox API retention cleanup failed'
              : 'repo snapshot archived and published via Dropbox API'
        : transferBackend === 'folder'
          ? hasFailures && retentionFailed
            ? 'Dropbox folder sync and retention cleanup failed'
            : hasFailures
              ? 'one or more Dropbox folder sync copies failed'
              : retentionFailed
                ? 'Dropbox folder sync retention cleanup failed'
                : apiAttemptFailed
                  ? 'Dropbox API upload failed, then the snapshot was staged in the Dropbox sync folder'
                  : 'repo snapshot archived and staged in the Dropbox sync folder'
          : tokenPresent
            ? syncFolderRoot
              ? 'Dropbox API and sync folder publishing are disabled'
              : 'Dropbox token is missing and no sync folder fallback is configured'
            : syncFolderRoot
              ? 'Dropbox token is missing; using sync folder fallback was not possible for this run'
              : 'Dropbox publishing is disabled'
      : 'no major repo changes were detected',
    majorChange: snapshotSummary.majorChange,
    manifestPath,
    archivePath,
    manifest,
    dropbox: {
      enabled: Boolean(tokenPresent || syncFolderRoot),
      root: dropboxRoot,
      syncFolderRoot,
      backend: transferBackend,
      retentionHistoryLimit: historyLimit,
      transfers,
      retention,
    },
  };

  if (outputDir.shouldCleanup && (!shouldPublish || (!hasFailures && !retentionFailed))) {
    rmSync(outputDir.path, { recursive: true, force: true });
  }

  return result;
}

async function main(): Promise<void> {
  const result = await runRepoDropboxSync({
    repoPath: process.env.REPO_PATH ?? process.env.CORI_REPO_PATH ?? repoRoot,
    commit: process.env.REPO_COMMIT ?? undefined,
    developerId: process.env.REPO_DEVELOPER_ID ?? process.env.GIT_AUTHOR_NAME ?? process.env.USER ?? 'unknown',
    dropboxRoot: process.env.REPO_DROPBOX_ROOT ?? process.env.DROPBOX_REPO_ROOT,
    syncFolderRoot: process.env.REPO_DROPBOX_SYNC_FOLDER_ROOT ?? process.env.DROPBOX_SYNC_FOLDER_ROOT ?? process.env.DROPBOX_FOLDER_ROOT,
    snapshotMode: process.env.REPO_DROPBOX_SNAPSHOT_MODE as RepoDropboxSnapshotMode | undefined,
    historyLimit: process.env.REPO_DROPBOX_HISTORY_LIMIT ? Number(process.env.REPO_DROPBOX_HISTORY_LIMIT) : undefined,
    publishToDropbox: true,
    outputDir: process.env.REPO_DROPBOX_SYNC_OUTPUT_DIR,
  });

  if (result.status === 'failed') {
    throw new Error(result.reason);
  }

  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

function isDirectExecution(): boolean {
  const entryPoint = process.argv[1];
  if (!entryPoint) {
    return false;
  }
  return resolve(entryPoint) === fileURLToPath(import.meta.url);
}

if (isDirectExecution()) {
  main().catch((error: unknown) => {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  });
}
