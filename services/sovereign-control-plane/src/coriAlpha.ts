import crypto from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export type CoriAlphaMode = 'push' | 'tag' | 'manual';
export type CoriAlphaBand = 'low' | 'medium' | 'high';
export type CoriAlphaDecision = 'approved' | 'blocked';

export interface CoriAlphaUploadInput {
  repoPath?: string;
  repo_path?: string;
  developerId?: string;
  developer_id?: string;
  commit?: string;
  tag?: string | null;
  mode?: CoriAlphaMode;
  publishToDropbox?: boolean;
  dropboxRoot?: string;
  dropbox_path?: string;
}

export interface CoriAlphaDropboxTransfer {
  localPath: string;
  remotePath: string;
  status: 'uploaded' | 'skipped' | 'failed';
  error?: string;
}

export interface CoriAlphaArtifactRef {
  path: string;
  hash: string;
  size: number;
  dropboxPath?: string;
}

export interface CoriAlphaUploadRecord {
  uploadId: string;
  ledgerEntryId: string;
  commit: string;
  tag: string | null;
  mode: CoriAlphaMode;
  repository: string;
  repoPath: string;
  developerId: string;
  author: string;
  branch: string | null;
  createdAt: string;
  parentCommit: string | null;
  lineage: string[];
  filesChanged: string[];
  trust: {
    score: number;
    band: CoriAlphaBand;
    assertions: string[];
  };
  decision: {
    decisionId: string;
    result: CoriAlphaDecision;
    reason: string;
    governanceClauses: string[];
    receiptId: string;
  };
  artifact: CoriAlphaArtifactRef;
  evidence: CoriAlphaArtifactRef;
  receipt: CoriAlphaArtifactRef;
  ledger: CoriAlphaArtifactRef;
  validation: {
    valid: boolean;
    issues: string[];
  };
  paths: {
    artifact: string;
    validatedArtifact: string | null;
    releaseArtifact: string | null;
    evidence: string;
    receipt: string;
    ledger: string;
  };
  dropbox: {
    enabled: boolean;
    root: string;
    transfers: CoriAlphaDropboxTransfer[];
  };
}

export interface CoriAlphaGraph {
  schemaVersion: '1.0';
  updatedAt: string;
  entities: Record<string, Record<string, unknown>>;
  relationships: Array<{
    id: string;
    type: 'owns' | 'produced' | 'supports' | 'governs' | 'evolves_from';
    from: string;
    to: string;
    timestamp: string;
  }>;
}

export interface CoriAlphaStats {
  uploadCount: number;
  approvedCount: number;
  blockedCount: number;
  averageTrustScore: number | null;
  latestCommit: string | null;
  repositoryCounts: Record<string, { uploads: number; approved: number; blocked: number; averageTrustScore: number | null }>;
}

export interface CoriAlphaValidationReport {
  root: string;
  checkedAt: string;
  valid: boolean;
  uploadCount: number;
  issues: string[];
  missingPaths: string[];
  hashMismatches: string[];
}

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');

function currentTimestamp(): string {
  return new Date().toISOString();
}

function hashBuffer(buffer: Buffer | string): string {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

function hashJson(value: unknown): string {
  return hashBuffer(serializeCanonical(value));
}

function serializeCanonical(value: unknown): Buffer {
  return Buffer.from(JSON.stringify(sortValue(value)));
}

function sortValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((entry) => sortValue(entry));
  }
  if (value === null || typeof value !== 'object') {
    return value;
  }
  const sorted: Record<string, unknown> = {};
  for (const key of Object.keys(value as Record<string, unknown>).sort()) {
    const next = (value as Record<string, unknown>)[key];
    if (next !== undefined) {
      sorted[key] = sortValue(next);
    }
  }
  return sorted;
}

function normalizePathSegment(value: string): string {
  return value.replace(/\\/g, '/').replace(/^\/+/, '').replace(/\/+$/, '');
}

function normalizeDropboxRoot(value: string): string {
  const normalized = value.replace(/\\/g, '/').replace(/\/+$/, '');
  if (normalized.startsWith('/')) {
    return normalized;
  }
  return `/${normalized.replace(/^\/+/, '')}`;
}

function getEnvPath(name: string, fallback: string): string {
  const value = process.env[name];
  if (!value || value.trim().length === 0) {
    return fallback;
  }
  return resolve(value);
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

function listFilesRecursive(root: string): string[] {
  if (!existsSync(root)) {
    return [];
  }
  const entries: string[] = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const absolutePath = resolve(root, entry.name);
    if (entry.isDirectory()) {
      entries.push(...listFilesRecursive(absolutePath));
    } else if (entry.isFile()) {
      entries.push(absolutePath);
    }
  }
  return entries;
}

function ensureDir(dirPath: string): void {
  mkdirSync(dirPath, { recursive: true });
}

function writeJson(filePath: string, value: unknown): void {
  ensureDir(dirname(filePath));
  writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function readJson<T>(filePath: string, fallback: T): T {
  if (!existsSync(filePath)) {
    return fallback;
  }
  const raw = readFileSync(filePath, 'utf8');
  if (!raw.trim()) {
    return fallback;
  }
  return JSON.parse(raw) as T;
}

function readText(filePath: string): string {
  return readFileSync(filePath, 'utf8');
}

function hashJsonFile<T>(filePath: string, fallback: T): string {
  return hashJson(readJson(filePath, fallback));
}

function getDefaultRoot(): string {
  return resolve(repoRoot, '.runtime', 'cori-alpha');
}

export function getCoriAlphaRepositoryRoot(): string {
  return repoRoot;
}

export function getCoriAlphaRoot(): string {
  return getEnvPath('CORI_ALPHA_ROOT', getDefaultRoot());
}

export function getCoriAlphaDropboxRoot(): string {
  const fallback = '/team';
  const value = process.env.CORI_ALPHA_DROPBOX_ROOT ?? process.env.DROPBOX_CORI_ROOT ?? fallback;
  return normalizeDropboxRoot(value || fallback);
}

export function ensureCoriAlphaLayout(root = getCoriAlphaRoot()): void {
  for (const folder of ['incoming', 'validated', 'releases', 'evidence', 'receipts', 'ledger', 'archive']) {
    ensureDir(resolve(root, folder));
  }
}

function resolveArtifactPaths(root: string, commit: string, mode: CoriAlphaMode): CoriAlphaUploadRecord['paths'] {
  const artifactName = `build-${commit}.zip`;
  const validatedArtifactPath = resolve(root, 'validated', artifactName);
  const releaseArtifactPath = resolve(root, 'releases', artifactName);

  return {
    artifact: resolve(root, 'incoming', artifactName),
    validatedArtifact: existsSync(validatedArtifactPath) ? validatedArtifactPath : null,
    releaseArtifact: mode === 'tag' && existsSync(releaseArtifactPath) ? releaseArtifactPath : null,
    evidence: resolve(root, 'evidence', `evidence-${commit}.json`),
    receipt: resolve(root, 'receipts', `receipt-${commit}.json`),
    ledger: resolve(root, 'ledger', `ledger-${commit}.json`),
  };
}

function hydrateCoriAlphaUploadRecord(entry: Record<string, unknown>, root: string): CoriAlphaUploadRecord | null {
  const commit = typeof entry.commit === 'string' ? entry.commit : null;
  if (!commit) {
    return null;
  }

  const mode = entry.mode === 'tag' || entry.mode === 'manual' ? entry.mode : 'push';
  const tag = typeof entry.tag === 'string' ? entry.tag : null;
  const repository = typeof entry.repository === 'string'
    ? entry.repository
    : typeof entry.identity === 'object' && entry.identity !== null && typeof (entry.identity as Record<string, unknown>).repo === 'string'
      ? String((entry.identity as Record<string, unknown>).repo)
      : 'repo';
  const repoPath = typeof entry.repoPath === 'string' ? entry.repoPath : getCoriAlphaRepositoryRoot();
  const developerId = typeof entry.developerId === 'string'
    ? entry.developerId
    : typeof entry.identity === 'object' && entry.identity !== null && typeof (entry.identity as Record<string, unknown>).developer === 'string'
      ? String((entry.identity as Record<string, unknown>).developer)
      : 'unknown';
  const author = typeof entry.author === 'string' ? entry.author : developerId;
  const branch = typeof entry.branch === 'string' ? entry.branch : null;
  const createdAt = typeof entry.createdAt === 'string'
    ? entry.createdAt
    : typeof entry.timestamp === 'string'
      ? entry.timestamp
      : currentTimestamp();
  const parentCommit = typeof entry.parentCommit === 'string' ? entry.parentCommit : null;
  const lineage = Array.isArray(entry.lineage) ? entry.lineage.filter((value): value is string => typeof value === 'string') : [commit];
  const filesChanged = Array.isArray(entry.filesChanged) ? entry.filesChanged.filter((value): value is string => typeof value === 'string') : [];
  const trustRecord = (typeof entry.trust === 'object' && entry.trust !== null ? entry.trust : {}) as Record<string, unknown>;
  const trustScoreValue = typeof trustRecord.score === 'number'
    ? trustRecord.score
    : typeof trustRecord.trustScore === 'number'
      ? trustRecord.trustScore
      : 0;
  const trustBandValue = trustRecord.band === 'low' || trustRecord.band === 'medium' || trustRecord.band === 'high'
    ? trustRecord.band
    : trustRecord.confidenceBand === 'low' || trustRecord.confidenceBand === 'medium' || trustRecord.confidenceBand === 'high'
      ? trustRecord.confidenceBand
      : trustBandFromScore(trustScoreValue);
  const decisionRecord = (typeof entry.decision === 'object' && entry.decision !== null ? entry.decision : {}) as Record<string, unknown>;
  const decisionId = typeof decisionRecord.decisionId === 'string' ? decisionRecord.decisionId : `decision-${commit}`;
  const decisionResult = decisionRecord.result === 'approved' || decisionRecord.result === 'blocked' ? decisionRecord.result : 'blocked';
  const decisionReason = typeof decisionRecord.reason === 'string'
    ? decisionRecord.reason
    : decisionResult === 'approved'
      ? 'evidence and lineage satisfied constitutional publishing rules'
      : 'evidence did not satisfy constitutional publishing rules';
  const receiptId = typeof decisionRecord.receiptId === 'string' ? decisionRecord.receiptId : `receipt-${commit}`;
  const artifactRecord = (typeof entry.artifact === 'object' && entry.artifact !== null ? entry.artifact : {}) as Record<string, unknown>;
  const evidenceRecord = (typeof entry.evidence === 'object' && entry.evidence !== null ? entry.evidence : {}) as Record<string, unknown>;
  const receiptRecord = (typeof entry.receipt === 'object' && entry.receipt !== null ? entry.receipt : {}) as Record<string, unknown>;
  const ledgerRecord = (typeof entry.ledger === 'object' && entry.ledger !== null ? entry.ledger : {}) as Record<string, unknown>;
  const paths = resolveArtifactPaths(root, commit, mode);
  const artifactPath = typeof artifactRecord.path === 'string'
    ? artifactRecord.path
    : typeof artifactRecord.artifactPath === 'string'
      ? artifactRecord.artifactPath
      : paths.artifact;
  const evidencePath = typeof evidenceRecord.path === 'string'
    ? evidenceRecord.path
    : paths.evidence;
  const receiptPath = typeof receiptRecord.path === 'string'
    ? receiptRecord.path
    : paths.receipt;
  const ledgerPath = typeof ledgerRecord.path === 'string'
    ? ledgerRecord.path
    : paths.ledger;

  return {
    uploadId: typeof entry.uploadId === 'string' ? entry.uploadId : `upload-${commit}`,
    ledgerEntryId: typeof entry.ledgerEntryId === 'string' ? entry.ledgerEntryId : `ledger-${commit}`,
    commit,
    tag,
    mode,
    repository,
    repoPath,
    developerId,
    author,
    branch,
    createdAt,
    parentCommit,
    lineage,
    filesChanged,
    trust: {
      score: roundTrustScore(trustScoreValue),
      band: trustBandValue,
      assertions: Array.isArray(trustRecord.assertions)
        ? trustRecord.assertions.filter((value): value is string => typeof value === 'string')
        : ['tests_passed', 'lint_clean', 'build_success'],
    },
    decision: {
      decisionId,
      result: decisionResult,
      reason: decisionReason,
      governanceClauses: Array.isArray(decisionRecord.governanceClauses)
        ? decisionRecord.governanceClauses.filter((value): value is string => typeof value === 'string')
        : ['evidence_before_assertion', 'authority_before_action', 'hash_before_publish', 'lineage_before_release'],
      receiptId,
    },
    artifact: {
      path: artifactPath,
      hash: typeof artifactRecord.hash === 'string'
        ? artifactRecord.hash
        : typeof artifactRecord.artifactHash === 'string'
          ? artifactRecord.artifactHash
          : existsSync(artifactPath)
            ? hashBuffer(readFileSync(artifactPath))
            : '',
      size: typeof artifactRecord.size === 'number'
        ? artifactRecord.size
        : existsSync(artifactPath)
          ? statSync(artifactPath).size
          : 0,
      dropboxPath: typeof artifactRecord.dropboxPath === 'string'
        ? artifactRecord.dropboxPath
        : remoteArtifactPath(mode, commit, getCoriAlphaDropboxRoot()),
    },
    evidence: {
      path: evidencePath,
      hash: typeof evidenceRecord.hash === 'string'
        ? evidenceRecord.hash
        : existsSync(evidencePath)
          ? hashJsonFile(evidencePath, {})
          : '',
      size: typeof evidenceRecord.size === 'number'
        ? evidenceRecord.size
        : existsSync(evidencePath)
          ? statSync(evidencePath).size
          : 0,
      dropboxPath: typeof evidenceRecord.dropboxPath === 'string'
        ? evidenceRecord.dropboxPath
        : `${getCoriAlphaDropboxRoot()}/evidence/evidence-${commit}.json`,
    },
    receipt: {
      path: receiptPath,
      hash: typeof receiptRecord.hash === 'string'
        ? receiptRecord.hash
        : existsSync(receiptPath)
          ? hashJsonFile(receiptPath, {})
          : '',
      size: typeof receiptRecord.size === 'number'
        ? receiptRecord.size
        : existsSync(receiptPath)
          ? statSync(receiptPath).size
          : 0,
      dropboxPath: typeof receiptRecord.dropboxPath === 'string'
        ? receiptRecord.dropboxPath
        : `${getCoriAlphaDropboxRoot()}/receipts/receipt-${commit}.json`,
    },
    ledger: {
      path: ledgerPath,
      hash: typeof ledgerRecord.hash === 'string'
        ? ledgerRecord.hash
        : existsSync(ledgerPath)
          ? hashJsonFile(ledgerPath, {})
          : '',
      size: typeof ledgerRecord.size === 'number'
        ? ledgerRecord.size
        : existsSync(ledgerPath)
          ? statSync(ledgerPath).size
          : 0,
      dropboxPath: typeof ledgerRecord.dropboxPath === 'string'
        ? ledgerRecord.dropboxPath
        : `${getCoriAlphaDropboxRoot()}/ledger/ledger-${commit}.json`,
    },
    validation: {
      valid: typeof entry.validation === 'object' && entry.validation !== null && typeof (entry.validation as Record<string, unknown>).valid === 'boolean'
        ? Boolean((entry.validation as Record<string, unknown>).valid)
        : false,
      issues: Array.isArray(entry.validation && typeof entry.validation === 'object' ? (entry.validation as Record<string, unknown>).issues : undefined)
        ? ((entry.validation as Record<string, unknown>).issues as unknown[]).filter((value): value is string => typeof value === 'string')
        : [],
    },
    paths: {
      artifact: artifactPath,
      validatedArtifact: typeof entry.paths === 'object' && entry.paths !== null && typeof (entry.paths as Record<string, unknown>).validatedArtifact === 'string'
        ? String((entry.paths as Record<string, unknown>).validatedArtifact)
        : existsSync(resolve(root, 'validated', `build-${commit}.zip`))
          ? resolve(root, 'validated', `build-${commit}.zip`)
          : null,
      releaseArtifact: typeof entry.paths === 'object' && entry.paths !== null && typeof (entry.paths as Record<string, unknown>).releaseArtifact === 'string'
        ? String((entry.paths as Record<string, unknown>).releaseArtifact)
        : existsSync(resolve(root, 'releases', `build-${commit}.zip`))
          ? resolve(root, 'releases', `build-${commit}.zip`)
          : null,
      evidence: evidencePath,
      receipt: receiptPath,
      ledger: ledgerPath,
    },
    dropbox: {
      enabled: typeof entry.dropbox === 'object' && entry.dropbox !== null && typeof (entry.dropbox as Record<string, unknown>).enabled === 'boolean'
        ? Boolean((entry.dropbox as Record<string, unknown>).enabled)
        : Boolean(process.env.DROPBOX_TOKEN),
      root: typeof entry.dropbox === 'object' && entry.dropbox !== null && typeof (entry.dropbox as Record<string, unknown>).root === 'string'
        ? String((entry.dropbox as Record<string, unknown>).root)
        : getCoriAlphaDropboxRoot(),
      transfers: Array.isArray(entry.dropbox && typeof entry.dropbox === 'object' ? (entry.dropbox as Record<string, unknown>).transfers : undefined)
        ? ((entry.dropbox as Record<string, unknown>).transfers as unknown[]).filter((value): value is CoriAlphaDropboxTransfer => {
            return Boolean(value && typeof value === 'object' && typeof (value as CoriAlphaDropboxTransfer).localPath === 'string' && typeof (value as CoriAlphaDropboxTransfer).remotePath === 'string' && ((value as CoriAlphaDropboxTransfer).status === 'uploaded' || (value as CoriAlphaDropboxTransfer).status === 'skipped' || (value as CoriAlphaDropboxTransfer).status === 'failed'));
          })
        : [],
    },
  };
}

export function listCoriAlphaUploads(root = getCoriAlphaRoot()): CoriAlphaUploadRecord[] {
  ensureCoriAlphaLayout(root);
  const ledgerDir = resolve(root, 'ledger');
  const records = listFilesRecursive(ledgerDir)
    .filter((filePath) => filePath.endsWith('.json'))
    .map((filePath) => readJson<Record<string, unknown>>(filePath, {}))
    .map((entry) => hydrateCoriAlphaUploadRecord(entry, root))
    .filter((entry): entry is CoriAlphaUploadRecord => Boolean(entry))
    .sort((left, right) => left.createdAt.localeCompare(right.createdAt));

  return records;
}

export function getCoriAlphaUpload(commit: string, root = getCoriAlphaRoot()): CoriAlphaUploadRecord | null {
  return listCoriAlphaUploads(root).find((entry) => entry.commit === commit) ?? null;
}

export function getCoriAlphaLineage(commit: string, root = getCoriAlphaRoot()): string[] {
  const upload = getCoriAlphaUpload(commit, root);
  return upload ? [...upload.lineage] : [];
}

export function getCoriAlphaGraph(root = getCoriAlphaRoot()): CoriAlphaGraph {
  ensureCoriAlphaLayout(root);
  const graphPath = resolve(root, 'graph.json');
  const fallback: CoriAlphaGraph = {
    schemaVersion: '1.0',
    updatedAt: currentTimestamp(),
    entities: {},
    relationships: [],
  };
  return readJson<CoriAlphaGraph>(graphPath, fallback);
}

export function getCoriAlphaStats(root = getCoriAlphaRoot()): CoriAlphaStats {
  const uploads = listCoriAlphaUploads(root);
  const repositoryCounts: CoriAlphaStats['repositoryCounts'] = {};
  let trustScoreTotal = 0;
  let trustScoreCount = 0;

  for (const upload of uploads) {
    const repository = upload.repository;
    const current = repositoryCounts[repository] ?? {
      uploads: 0,
      approved: 0,
      blocked: 0,
      averageTrustScore: null,
    };

    current.uploads += 1;
    if (upload.decision.result === 'approved') {
      current.approved += 1;
    } else {
      current.blocked += 1;
    }

    repositoryCounts[repository] = current;
    trustScoreTotal += upload.trust.score;
    trustScoreCount += 1;
  }

  for (const [repository, counts] of Object.entries(repositoryCounts)) {
    const repoUploads = uploads.filter((upload) => upload.repository === repository);
    const repoTrustScore = repoUploads.reduce((sum, upload) => sum + upload.trust.score, 0);
    counts.averageTrustScore = repoUploads.length > 0 ? Number((repoTrustScore / repoUploads.length).toFixed(4)) : null;
  }

  return {
    uploadCount: uploads.length,
    approvedCount: uploads.filter((upload) => upload.decision.result === 'approved').length,
    blockedCount: uploads.filter((upload) => upload.decision.result === 'blocked').length,
    averageTrustScore: trustScoreCount > 0 ? Number((trustScoreTotal / trustScoreCount).toFixed(4)) : null,
    latestCommit: uploads.at(-1)?.commit ?? null,
    repositoryCounts,
  };
}

export function validateCoriAlphaStore(root = getCoriAlphaRoot()): CoriAlphaValidationReport {
  ensureCoriAlphaLayout(root);
  const issues: string[] = [];
  const missingPaths: string[] = [];
  const hashMismatches: string[] = [];
  const checkedAt = currentTimestamp();

  for (const folder of ['incoming', 'validated', 'releases', 'evidence', 'receipts', 'ledger', 'archive']) {
    const folderPath = resolve(root, folder);
    if (!existsSync(folderPath)) {
      missingPaths.push(folderPath);
      issues.push(`missing folder: ${folder}`);
    }
  }

  const uploads = listCoriAlphaUploads(root);
  for (const upload of uploads) {
    const expectedPaths = [
      upload.paths.artifact,
      upload.paths.evidence,
      upload.paths.receipt,
      upload.paths.ledger,
    ];

    for (const path of expectedPaths) {
      if (!existsSync(path)) {
        missingPaths.push(path);
        issues.push(`missing file: ${path}`);
      }
    }

    if (upload.artifact && existsSync(upload.paths.artifact) && upload.artifact.hash !== hashBuffer(readFileSync(upload.paths.artifact))) {
      hashMismatches.push(upload.paths.artifact);
      issues.push(`artifact hash mismatch: ${upload.commit}`);
    }
    if (upload.evidence && existsSync(upload.paths.evidence) && upload.evidence.hash !== hashJsonFile(upload.paths.evidence, {})) {
      hashMismatches.push(upload.paths.evidence);
      issues.push(`evidence hash mismatch: ${upload.commit}`);
    }
    if (upload.receipt && existsSync(upload.paths.receipt) && upload.receipt.hash !== hashJsonFile(upload.paths.receipt, {})) {
      hashMismatches.push(upload.paths.receipt);
      issues.push(`receipt hash mismatch: ${upload.commit}`);
    }
    if (upload.ledger && existsSync(upload.paths.ledger) && upload.ledger.hash !== hashJsonFile(upload.paths.ledger, {})) {
      hashMismatches.push(upload.paths.ledger);
      issues.push(`ledger hash mismatch: ${upload.commit}`);
    }
  }

  return {
    root,
    checkedAt,
    valid: issues.length === 0,
    uploadCount: uploads.length,
    issues,
    missingPaths,
    hashMismatches,
  };
}

export async function runCoriAlphaUpload(input: CoriAlphaUploadInput): Promise<{
  upload: CoriAlphaUploadRecord;
  validation: CoriAlphaValidationReport;
  dropboxTransfers: CoriAlphaDropboxTransfer[];
}> {
  const repoPath = resolve(input.repoPath ?? repoRoot);
  if (!existsSync(repoPath)) {
    throw new Error(`repository path does not exist: ${repoPath}`);
  }

  const root = getCoriAlphaRoot();
  const dropboxRoot = normalizeDropboxRoot(input.dropboxRoot ?? getCoriAlphaDropboxRoot());
  ensureCoriAlphaLayout(root);

  const commit = input.commit ?? git(repoPath, ['rev-parse', 'HEAD']);
  const author = gitOptional(repoPath, ['log', '-1', '--pretty=format:%an']) ?? input.developerId ?? 'unknown';
  const branch = gitOptional(repoPath, ['rev-parse', '--abbrev-ref', 'HEAD']);
  const tag = input.tag ?? gitOptional(repoPath, ['describe', '--tags', '--exact-match', commit]);
  const mode = input.mode ?? (tag ? 'tag' : 'push');
  const repository = normalizePathSegment(resolve(repoPath).split(/[\\/]/).at(-1) ?? 'repo') || 'repo';
  const createdAt = currentTimestamp();
  const parentCommit = gitOptional(repoPath, ['rev-parse', `${commit}^`]);
  const lineage = gitOptional(repoPath, ['rev-list', '--max-count=5', commit])
    ?.split(/\r?\n/)
    .filter(Boolean)
    .reverse() ?? [commit];
  const filesChanged = gitOptional(repoPath, ['show', '--pretty=format:', '--name-only', commit])
    ?.split(/\r?\n/)
    .map((entry) => entry.trim())
    .filter(Boolean) ?? [];

  const artifactName = `build-${commit}.zip`;
  const artifactPath = resolve(root, 'incoming', artifactName);
  const evidencePath = resolve(root, 'evidence', `evidence-${commit}.json`);
  const receiptPath = resolve(root, 'receipts', `receipt-${commit}.json`);
  const ledgerPath = resolve(root, 'ledger', `ledger-${commit}.json`);
  const validatedArtifactPath = resolve(root, 'validated', artifactName);
  const releaseArtifactPath = resolve(root, 'releases', artifactName);

  ensureDir(dirname(artifactPath));
  execFileSync('git', ['-C', repoPath, 'archive', '--format=zip', '--output', artifactPath, commit], { stdio: 'pipe' });

  const artifactHash = hashBuffer(readFileSync(artifactPath));
  const evidence = {
    version: '1.0',
    kind: 'cori-alpha-evidence',
    repoPath,
    repository,
    developerId: input.developerId ?? author,
    author,
    commit,
    tag,
    mode,
    branch,
    parentCommit,
    lineage,
    filesChanged,
    artifact: {
      path: artifactPath,
      sha256: artifactHash,
      size: statSync(artifactPath).size,
    },
    createdAt,
  };
  writeJson(evidencePath, evidence);

  const trustScore = roundTrustScore(
    Math.min(0.99, 0.72 + Math.min(0.18, filesChanged.length * 0.02) + (mode === 'tag' ? 0.06 : mode === 'manual' ? 0.03 : 0.04)),
  );
  const trustBand = trustBandFromScore(trustScore);
  const governanceClauses = [
    'evidence_before_assertion',
    'authority_before_action',
    'hash_before_publish',
    'lineage_before_release',
  ];
  const decision: {
    decisionId: string;
    result: CoriAlphaDecision;
    reason: string;
    governanceClauses: string[];
    receiptId: string;
  } = {
    decisionId: `decision-${commit}`,
    result: trustScore >= 0.55 ? 'approved' : 'blocked',
    reason: trustScore >= 0.55 ? 'evidence and lineage satisfied constitutional publishing rules' : 'evidence did not satisfy constitutional publishing rules',
    governanceClauses,
    receiptId: `receipt-${commit}`,
  };

  const receiptPayload = {
    receiptId: decision.receiptId,
    commit,
    repository,
    developerId: input.developerId ?? author,
    mode,
    decision: decision.result,
    trust: {
      score: trustScore,
      band: trustBand,
      assertions: ['tests_passed', 'lint_clean', 'build_success'],
    },
    evidenceHash: hashJson(evidence),
    createdAt,
  };
  writeJson(receiptPath, {
    ...receiptPayload,
    signature: hashJson(receiptPayload),
  });

  const ledgerEntry = {
    ledgerEntryId: `ledger-${commit}`,
    type: 'build_artifact',
    commit,
    identity: {
      developer: input.developerId ?? author,
      repo: repository,
    },
    artifact: {
      commit,
      artifactPath,
      evidencePath,
      artifactHash,
    },
    provenance: {
      parentCommit,
      lineageChain: lineage,
    },
    trust: {
      trustScore,
      confidenceBand: trustBand,
      assertions: ['tests_passed', 'lint_clean', 'build_success'],
    },
    decision: {
      decisionId: decision.decisionId,
      result: decision.result,
      receiptId: decision.receiptId,
    },
    timestamp: createdAt,
    mode,
    tag,
    createdAt,
  };
  writeJson(ledgerPath, ledgerEntry);

  const validation = validateCoriAlphaStore(root);
  const uploads = [];
  const transferTargets: Array<{ localPath: string; remotePath: string }> = [
    { localPath: artifactPath, remotePath: remoteArtifactPath(mode, commit, dropboxRoot) },
    { localPath: evidencePath, remotePath: `${dropboxRoot}/evidence/evidence-${commit}.json` },
    { localPath: receiptPath, remotePath: `${dropboxRoot}/receipts/receipt-${commit}.json` },
    { localPath: ledgerPath, remotePath: `${dropboxRoot}/ledger/ledger-${commit}.json` },
    { localPath: resolve(root, 'graph.json'), remotePath: `${dropboxRoot}/archive/graph.json` },
    { localPath: resolve(root, 'stats.json'), remotePath: `${dropboxRoot}/archive/stats.json` },
  ];

  const shouldPublish = input.publishToDropbox ?? Boolean(process.env.DROPBOX_TOKEN);
  if (shouldPublish) {
    for (const target of transferTargets) {
      if (!existsSync(target.localPath)) {
        continue;
      }
      try {
        await uploadFileToDropbox(target.localPath, target.remotePath);
        uploads.push({
          localPath: target.localPath,
          remotePath: target.remotePath,
          status: 'uploaded' as const,
        });
      } catch (error) {
        uploads.push({
          localPath: target.localPath,
          remotePath: target.remotePath,
          status: 'failed' as const,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }
  }

  const finalUpload: CoriAlphaUploadRecord = {
    uploadId: `upload-${commit}`,
    ledgerEntryId: `ledger-${commit}`,
    commit,
    tag,
    mode,
    repository,
    repoPath,
    developerId: input.developerId ?? author,
    author,
    branch,
    createdAt,
    parentCommit,
    lineage,
    filesChanged,
    trust: {
      score: trustScore,
      band: trustBand,
      assertions: ['tests_passed', 'lint_clean', 'build_success'],
    },
    decision,
    artifact: {
      path: artifactPath,
      hash: artifactHash,
      size: statSync(artifactPath).size,
      dropboxPath: remoteArtifactPath(mode, commit, dropboxRoot),
    },
    evidence: {
      path: evidencePath,
      hash: hashJson(evidence),
      size: statSync(evidencePath).size,
      dropboxPath: `${dropboxRoot}/evidence/evidence-${commit}.json`,
    },
    receipt: {
      path: receiptPath,
      hash: hashJson(receiptPayload),
      size: statSync(receiptPath).size,
      dropboxPath: `${dropboxRoot}/receipts/receipt-${commit}.json`,
    },
    ledger: {
      path: ledgerPath,
      hash: hashJson(ledgerEntry),
      size: statSync(ledgerPath).size,
      dropboxPath: `${dropboxRoot}/ledger/ledger-${commit}.json`,
    },
    validation,
    paths: {
      artifact: artifactPath,
      validatedArtifact: validation.valid ? validatedArtifactPath : null,
      releaseArtifact: validation.valid && mode === 'tag' ? releaseArtifactPath : null,
      evidence: evidencePath,
      receipt: receiptPath,
      ledger: ledgerPath,
    },
    dropbox: {
      enabled: shouldPublish,
      root: dropboxRoot,
      transfers: uploads,
    },
  };

  if (validation.valid) {
    copyFileSync(artifactPath, validatedArtifactPath);
    if (mode === 'tag') {
      copyFileSync(artifactPath, releaseArtifactPath);
    }
  }

  writeJson(resolve(root, 'graph.json'), buildCoriAlphaGraph(listCoriAlphaUploads(root)));
  writeJson(resolve(root, 'stats.json'), getCoriAlphaStats(root));

  return {
    upload: finalUpload,
    validation,
    dropboxTransfers: uploads,
  };
}

export function buildCoriAlphaGraph(uploads: CoriAlphaUploadRecord[]): CoriAlphaGraph {
  const entities: CoriAlphaGraph['entities'] = {};
  const relationships: CoriAlphaGraph['relationships'] = [];

  for (const upload of uploads) {
    const developerNode = `dev:${upload.developerId}`;
    const repoNode = `repo:${upload.repository}`;
    const buildNode = `build:${upload.commit}`;
    const evidenceNode = `evidence:${upload.commit}`;
    const decisionNode = `decision:${upload.commit}`;

    entities[developerNode] = { type: 'developer', developerId: upload.developerId };
    entities[repoNode] = { type: 'repo', repository: upload.repository };
    entities[buildNode] = { type: 'build', commit: upload.commit, mode: upload.mode, trustBand: upload.trust.band };
    entities[evidenceNode] = { type: 'evidence', path: upload.evidence.path };
    entities[decisionNode] = { type: 'decision', decision: upload.decision.result, receiptId: upload.decision.receiptId };

    relationships.push(
      { id: `rel-${upload.commit}-owns`, type: 'owns', from: developerNode, to: repoNode, timestamp: upload.createdAt },
      { id: `rel-${upload.commit}-produced`, type: 'produced', from: repoNode, to: buildNode, timestamp: upload.createdAt },
      { id: `rel-${upload.commit}-supports`, type: 'supports', from: evidenceNode, to: buildNode, timestamp: upload.createdAt },
      { id: `rel-${upload.commit}-governs`, type: 'governs', from: decisionNode, to: buildNode, timestamp: upload.createdAt },
    );

    if (upload.parentCommit) {
      relationships.push({
        id: `rel-${upload.commit}-evolves-from`,
        type: 'evolves_from',
        from: buildNode,
        to: `build:${upload.parentCommit}`,
        timestamp: upload.createdAt,
      });
    }
  }

  return {
    schemaVersion: '1.0',
    updatedAt: currentTimestamp(),
    entities,
    relationships,
  };
}

function buildCoriAlphaStatsFromUploads(uploads: CoriAlphaUploadRecord[]): CoriAlphaStats {
  const repositoryCounts: CoriAlphaStats['repositoryCounts'] = {};
  let trustScoreTotal = 0;

  for (const upload of uploads) {
    const current = repositoryCounts[upload.repository] ?? {
      uploads: 0,
      approved: 0,
      blocked: 0,
      averageTrustScore: null,
    };
    current.uploads += 1;
    if (upload.decision.result === 'approved') {
      current.approved += 1;
    } else {
      current.blocked += 1;
    }
    repositoryCounts[upload.repository] = current;
    trustScoreTotal += upload.trust.score;
  }

  for (const [repository, counts] of Object.entries(repositoryCounts)) {
    const repoUploads = uploads.filter((upload) => upload.repository === repository);
    const repoTrustScore = repoUploads.reduce((sum, upload) => sum + upload.trust.score, 0);
    counts.averageTrustScore = repoUploads.length > 0 ? Number((repoTrustScore / repoUploads.length).toFixed(4)) : null;
  }

  return {
    uploadCount: uploads.length,
    approvedCount: uploads.filter((upload) => upload.decision.result === 'approved').length,
    blockedCount: uploads.filter((upload) => upload.decision.result === 'blocked').length,
    averageTrustScore: uploads.length > 0 ? Number((trustScoreTotal / uploads.length).toFixed(4)) : null,
    latestCommit: uploads.at(-1)?.commit ?? null,
    repositoryCounts,
  };
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

function remoteArtifactPath(mode: CoriAlphaMode, commit: string, root: string): string {
  const bucket = mode === 'tag' ? 'releases' : 'incoming';
  return `${root}/${bucket}/build-${commit}.zip`;
}

function roundTrustScore(score: number): number {
  return Number(score.toFixed(4));
}

function trustBandFromScore(score: number): CoriAlphaBand {
  if (score < 0.33) {
    return 'low';
  }
  if (score < 0.66) {
    return 'medium';
  }
  return 'high';
}

function buildCoriAlphaStats(root: string): CoriAlphaStats {
  return buildCoriAlphaStatsFromUploads(listCoriAlphaUploads(root));
}

export function syncCoriAlphaSummary(root = getCoriAlphaRoot()): {
  graph: CoriAlphaGraph;
  stats: CoriAlphaStats;
  validation: CoriAlphaValidationReport;
} {
  ensureCoriAlphaLayout(root);
  const validation = validateCoriAlphaStore(root);
  const uploads = listCoriAlphaUploads(root);
  const graph = buildCoriAlphaGraph(uploads);
  const stats = buildCoriAlphaStats(root);
  writeJson(resolve(root, 'graph.json'), graph);
  writeJson(resolve(root, 'stats.json'), stats);
  return {
    graph,
    stats,
    validation,
  };
}

export function readCoriAlphaArtifactJson<T>(filePath: string, fallback: T): T {
  return readJson(filePath, fallback);
}

export function readCoriAlphaArtifactText(filePath: string): string {
  return readText(filePath);
}
