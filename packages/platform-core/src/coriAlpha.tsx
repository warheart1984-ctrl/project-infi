import crypto from 'node:crypto';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import type { CSSProperties, ReactNode } from 'react';

export type CoriAlphaBand = 'low' | 'medium' | 'high';

export type CoriAlphaDecision = 'approved' | 'blocked';

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
  mode: 'push' | 'tag' | 'manual';
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
    transfers: { localPath: string; remotePath: string; status: 'uploaded' | 'skipped' | 'failed'; error?: string }[];
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
  repositoryCounts: Record<
    string,
    {
      uploads: number;
      approved: number;
      blocked: number;
      averageTrustScore: number | null;
    }
  >;
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

export interface CoriAlphaWorkspaceSummary {
  root: string;
  uploads: CoriAlphaUploadRecord[];
  summary: CoriAlphaStats;
  validation: CoriAlphaValidationReport;
  graph: CoriAlphaGraph;
}

export interface CoriAlphaSummaryCardProps {
  summary: CoriAlphaWorkspaceSummary | null;
  loading?: boolean;
  title?: string;
  surfaceLabel?: string;
  emptyMessage: string;
  loadingMessage?: string;
}

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');

function currentTimestamp(): string {
  return new Date().toISOString();
}

function getDefaultRoot(): string {
  return resolve(packageRoot, '..', '.runtime', 'cori-alpha');
}

export function getCoriAlphaRoot(): string {
  const value = process.env.CORI_ALPHA_ROOT;
  if (value && value.trim()) {
    return resolve(value);
  }
  return getDefaultRoot();
}

function ensureCoriAlphaLayout(root: string): void {
  for (const folder of ['incoming', 'validated', 'releases', 'evidence', 'receipts', 'ledger', 'archive']) {
    const folderPath = resolve(root, folder);
    if (!existsSync(folderPath)) {
      continue;
    }
  }
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

function hashJson(value: unknown): string {
  return crypto.createHash('sha256').update(JSON.stringify(sortValue(value))).digest('hex');
}

function hashBuffer(buffer: Buffer | string): string {
  return crypto.createHash('sha256').update(buffer).digest('hex');
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

function hydrateUploadRecord(entry: Record<string, unknown>, root: string): CoriAlphaUploadRecord | null {
  const commit = typeof entry.commit === 'string' ? entry.commit : null;
  if (!commit) {
    return null;
  }

  const mode = entry.mode === 'tag' || entry.mode === 'manual' ? entry.mode : 'push';
  const repository = typeof entry.repository === 'string'
    ? entry.repository
    : typeof entry.identity === 'object' && entry.identity !== null && typeof (entry.identity as Record<string, unknown>).repo === 'string'
      ? String((entry.identity as Record<string, unknown>).repo)
      : 'repo';
  const repoPath = typeof entry.repoPath === 'string' ? entry.repoPath : getCoriAlphaRoot();
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
  const lineage = Array.isArray(entry.lineage)
    ? entry.lineage.filter((value): value is string => typeof value === 'string')
    : [commit];
  const filesChanged = Array.isArray(entry.filesChanged)
    ? entry.filesChanged.filter((value): value is string => typeof value === 'string')
    : [];
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
  const artifactPath = typeof artifactRecord.path === 'string'
    ? artifactRecord.path
    : typeof artifactRecord.artifactPath === 'string'
      ? artifactRecord.artifactPath
      : resolve(root, 'incoming', `build-${commit}.zip`);
  const evidencePath = typeof evidenceRecord.path === 'string' ? evidenceRecord.path : resolve(root, 'evidence', `evidence-${commit}.json`);
  const receiptPath = typeof receiptRecord.path === 'string' ? receiptRecord.path : resolve(root, 'receipts', `receipt-${commit}.json`);
  const ledgerPath = typeof ledgerRecord.path === 'string' ? ledgerRecord.path : resolve(root, 'ledger', `ledger-${commit}.json`);
  const validatedArtifactPath = resolve(root, 'validated', `build-${commit}.zip`);
  const releaseArtifactPath = resolve(root, 'releases', `build-${commit}.zip`);

  return {
    uploadId: typeof entry.uploadId === 'string' ? entry.uploadId : `upload-${commit}`,
    ledgerEntryId: typeof entry.ledgerEntryId === 'string' ? entry.ledgerEntryId : `ledger-${commit}`,
    commit,
    tag: typeof entry.tag === 'string' ? entry.tag : null,
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
        : existsSync(artifactPath)
          ? hashBuffer(readFileSync(artifactPath))
          : '',
      size: typeof artifactRecord.size === 'number'
        ? artifactRecord.size
        : existsSync(artifactPath)
          ? statSync(artifactPath).size
          : 0,
      dropboxPath: typeof artifactRecord.dropboxPath === 'string' ? artifactRecord.dropboxPath : undefined,
    },
    evidence: {
      path: evidencePath,
      hash: typeof evidenceRecord.hash === 'string'
        ? evidenceRecord.hash
        : existsSync(evidencePath)
          ? hashJson(readJson(evidencePath, {}))
          : '',
      size: typeof evidenceRecord.size === 'number'
        ? evidenceRecord.size
        : existsSync(evidencePath)
          ? statSync(evidencePath).size
          : 0,
      dropboxPath: typeof evidenceRecord.dropboxPath === 'string' ? evidenceRecord.dropboxPath : undefined,
    },
    receipt: {
      path: receiptPath,
      hash: typeof receiptRecord.hash === 'string'
        ? receiptRecord.hash
        : existsSync(receiptPath)
          ? hashJson(readJson(receiptPath, {}))
          : '',
      size: typeof receiptRecord.size === 'number'
        ? receiptRecord.size
        : existsSync(receiptPath)
          ? statSync(receiptPath).size
          : 0,
      dropboxPath: typeof receiptRecord.dropboxPath === 'string' ? receiptRecord.dropboxPath : undefined,
    },
    ledger: {
      path: ledgerPath,
      hash: typeof ledgerRecord.hash === 'string'
        ? ledgerRecord.hash
        : existsSync(ledgerPath)
          ? hashJson(readJson(ledgerPath, {}))
          : '',
      size: typeof ledgerRecord.size === 'number'
        ? ledgerRecord.size
        : existsSync(ledgerPath)
          ? statSync(ledgerPath).size
          : 0,
      dropboxPath: typeof ledgerRecord.dropboxPath === 'string' ? ledgerRecord.dropboxPath : undefined,
    },
    validation: {
      valid: typeof entry.validation === 'object' && entry.validation !== null && typeof (entry.validation as Record<string, unknown>).valid === 'boolean'
        ? Boolean((entry.validation as Record<string, unknown>).valid)
        : true,
      issues: Array.isArray(typeof entry.validation === 'object' && entry.validation !== null ? (entry.validation as Record<string, unknown>).issues : undefined)
        ? ((entry.validation as Record<string, unknown>).issues as unknown[]).filter((value): value is string => typeof value === 'string')
        : [],
    },
    paths: {
      artifact: artifactPath,
      validatedArtifact: existsSync(validatedArtifactPath) ? validatedArtifactPath : null,
      releaseArtifact: existsSync(releaseArtifactPath) ? releaseArtifactPath : null,
      evidence: evidencePath,
      receipt: receiptPath,
      ledger: ledgerPath,
    },
    dropbox: {
      enabled: typeof entry.dropbox === 'object' && entry.dropbox !== null && typeof (entry.dropbox as Record<string, unknown>).enabled === 'boolean'
        ? Boolean((entry.dropbox as Record<string, unknown>).enabled)
        : false,
      root: typeof entry.dropbox === 'object' && entry.dropbox !== null && typeof (entry.dropbox as Record<string, unknown>).root === 'string'
        ? String((entry.dropbox as Record<string, unknown>).root)
        : '/team',
      transfers: Array.isArray(typeof entry.dropbox === 'object' && entry.dropbox !== null ? (entry.dropbox as Record<string, unknown>).transfers : undefined)
        ? ((entry.dropbox as Record<string, unknown>).transfers as unknown[]).filter((value): value is { localPath: string; remotePath: string; status: 'uploaded' | 'skipped' | 'failed'; error?: string } => {
            return Boolean(value && typeof value === 'object' && typeof (value as { localPath?: unknown }).localPath === 'string' && typeof (value as { remotePath?: unknown }).remotePath === 'string');
          })
        : [],
    },
  };
}

export function listCoriAlphaUploads(root = getCoriAlphaRoot()): CoriAlphaUploadRecord[] {
  ensureCoriAlphaLayout(root);
  const ledgerDir = resolve(root, 'ledger');
  if (!existsSync(ledgerDir)) {
    return [];
  }

  return readdirSync(ledgerDir)
    .filter((entry) => entry.endsWith('.json'))
    .map((entry) => readJson<Record<string, unknown>>(resolve(ledgerDir, entry), {}))
    .map((entry) => hydrateUploadRecord(entry, root))
    .filter((entry): entry is CoriAlphaUploadRecord => Boolean(entry))
    .sort((left, right) => left.createdAt.localeCompare(right.createdAt));
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

function summarizeUploads(uploads: CoriAlphaUploadRecord[]): CoriAlphaStats {
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

function validateUploads(root: string, uploads: CoriAlphaUploadRecord[]): CoriAlphaValidationReport {
  const issues: string[] = [];
  const missingPaths: string[] = [];
  const hashMismatches: string[] = [];

  for (const upload of uploads) {
    const expectedPaths = [upload.paths.artifact, upload.paths.evidence, upload.paths.receipt, upload.paths.ledger];
    for (const expectedPath of expectedPaths) {
      if (!existsSync(expectedPath)) {
        missingPaths.push(expectedPath);
        issues.push(`missing file: ${expectedPath}`);
      }
    }

    if (existsSync(upload.paths.artifact) && upload.artifact.hash && upload.artifact.hash !== hashBuffer(readFileSync(upload.paths.artifact))) {
      hashMismatches.push(upload.paths.artifact);
      issues.push(`artifact hash mismatch: ${upload.commit}`);
    }
    if (existsSync(upload.paths.evidence) && upload.evidence.hash && upload.evidence.hash !== hashJson(readJson(upload.paths.evidence, {}))) {
      hashMismatches.push(upload.paths.evidence);
      issues.push(`evidence hash mismatch: ${upload.commit}`);
    }
    if (existsSync(upload.paths.receipt) && upload.receipt.hash && upload.receipt.hash !== hashJson(readJson(upload.paths.receipt, {}))) {
      hashMismatches.push(upload.paths.receipt);
      issues.push(`receipt hash mismatch: ${upload.commit}`);
    }
    if (existsSync(upload.paths.ledger) && upload.ledger.hash && upload.ledger.hash !== hashJson(readJson(upload.paths.ledger, {}))) {
      hashMismatches.push(upload.paths.ledger);
      issues.push(`ledger hash mismatch: ${upload.commit}`);
    }
  }

  return {
    root,
    checkedAt: currentTimestamp(),
    valid: issues.length === 0,
    uploadCount: uploads.length,
    issues,
    missingPaths,
    hashMismatches,
  };
}

export function getCoriAlphaWorkspaceSummary(root = getCoriAlphaRoot()): CoriAlphaWorkspaceSummary {
  ensureCoriAlphaLayout(root);
  const uploads = listCoriAlphaUploads(root);
  const graph = buildCoriAlphaGraph(uploads);
  const summary = summarizeUploads(uploads);
  const validation = validateUploads(root, uploads);
  return {
    root,
    uploads,
    summary,
    validation,
    graph,
  };
}

export interface CoriAlphaSummaryCardProps {
  summary: CoriAlphaWorkspaceSummary | null;
  loading?: boolean;
  title?: string;
  surfaceLabel?: string;
  emptyMessage: string;
  loadingMessage?: string;
}

export function CoriAlphaSummaryCard({
  summary,
  loading = false,
  title = 'CORI Alpha upload intelligence',
  surfaceLabel = 'Shared across ops-console and the customer workspace',
  emptyMessage,
  loadingMessage = 'Loading CORI Alpha upload intelligence...',
}: CoriAlphaSummaryCardProps) {
  return (
    <section style={cardStyle}>
      <div style={eyebrowStyle}>{surfaceLabel}</div>
      <h2 style={headingStyle}>{title}</h2>
      {loading ? (
        <p style={subtleStyle}>{loadingMessage}</p>
      ) : summary ? (
        <>
          <div style={metricGridStyle}>
            <Metric label="Uploads" value={String(summary.summary.uploadCount)} />
            <Metric label="Approved" value={String(summary.summary.approvedCount)} />
            <Metric label="Blocked" value={String(summary.summary.blockedCount)} />
            <Metric label="Avg trust" value={summary.summary.averageTrustScore === null ? 'n/a' : summary.summary.averageTrustScore.toFixed(4)} />
            <Metric label="Latest commit" value={summary.summary.latestCommit ?? 'none'} />
            <Metric label="Validation" value={summary.validation.valid ? 'pass' : 'review'} />
          </div>
          <section style={subpanelGridStyle}>
            <Panel title="Repository rollup">
              <div style={{ overflowX: 'auto' }}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Repository</th>
                      <th style={thStyle}>Uploads</th>
                      <th style={thStyle}>Approved</th>
                      <th style={thStyle}>Blocked</th>
                      <th style={thStyle}>Avg trust</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(summary.summary.repositoryCounts)
                      .sort(([left], [right]) => left.localeCompare(right))
                      .map(([repository, counts]) => (
                        <tr key={repository}>
                          <td style={tdStyle}>{repository}</td>
                          <td style={tdStyle}>{counts.uploads}</td>
                          <td style={tdStyle}>{counts.approved}</td>
                          <td style={tdStyle}>{counts.blocked}</td>
                          <td style={tdStyle}>{counts.averageTrustScore === null ? 'n/a' : counts.averageTrustScore.toFixed(4)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </Panel>

            <Panel title="Recent uploads">
              {summary.uploads.length ? (
                <div style={{ overflowX: 'auto' }}>
                  <table style={tableStyle}>
                    <thead>
                      <tr>
                        <th style={thStyle}>Commit</th>
                        <th style={thStyle}>Decision</th>
                        <th style={thStyle}>Trust</th>
                        <th style={thStyle}>Mode</th>
                        <th style={thStyle}>Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.uploads.slice(-5).reverse().map((upload) => (
                        <tr key={upload.commit}>
                          <td style={tdStyle}>{upload.commit.slice(0, 12)}</td>
                          <td style={tdStyle}>{upload.decision.result}</td>
                          <td style={tdStyle}>{upload.trust.band} ({upload.trust.score.toFixed(4)})</td>
                          <td style={tdStyle}>{upload.mode}{upload.tag ? ` · ${upload.tag}` : ''}</td>
                          <td style={tdStyle}>{upload.createdAt}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p style={subtleStyle}>No CORI Alpha uploads have been recorded yet.</p>
              )}
            </Panel>

            <Panel title="Validation report">
              <div style={metricGridStyle}>
                <Metric label="Valid" value={summary.validation.valid ? 'yes' : 'no'} />
                <Metric label="Checked at" value={summary.validation.checkedAt} />
                <Metric label="Issues" value={String(summary.validation.issues.length)} />
                <Metric label="Hash mismatches" value={String(summary.validation.hashMismatches.length)} />
              </div>
              {summary.validation.issues.length ? (
                <ul style={listStyle}>
                  {summary.validation.issues.map((issue) => (
                    <li key={issue}>{issue}</li>
                  ))}
                </ul>
              ) : (
                <p style={subtleStyle}>The current CORI Alpha store validates cleanly.</p>
              )}
            </Panel>
          </section>
          <p style={subtleStyle}>
            This is the same upload intelligence surface used by the operator console and the customer workspace, backed by the shared CORI Alpha ledger in `.runtime/cori-alpha`.
          </p>
        </>
      ) : (
        <p style={subtleStyle}>{emptyMessage}</p>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={metricStyle}>
      <div style={metricLabelStyle}>{label}</div>
      <div style={metricValueStyle}>{value}</div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={panelStyle}>
      <h3 style={panelHeadingStyle}>{title}</h3>
      {children}
    </div>
  );
}

const cardStyle: CSSProperties = {
  borderRadius: 24,
  padding: 24,
  background: 'rgba(255,255,255,0.92)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  boxShadow: '0 18px 42px rgba(15, 23, 42, 0.05)',
};

const eyebrowStyle: CSSProperties = {
  display: 'inline-flex',
  padding: '8px 12px',
  borderRadius: 999,
  fontSize: 12,
  fontWeight: 800,
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
  color: '#115e59',
  background: 'rgba(15, 118, 110, 0.12)',
};

const headingStyle: CSSProperties = {
  marginTop: 12,
  marginBottom: 12,
  fontSize: '1.35rem',
};

const subtleStyle: CSSProperties = {
  color: '#475569',
  lineHeight: 1.7,
};

const metricGridStyle: CSSProperties = {
  display: 'grid',
  gap: 10,
  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
};

const metricStyle: CSSProperties = {
  padding: 12,
  borderRadius: 16,
  background: '#f8fafc',
  border: '1px solid #e2e8f0',
};

const metricLabelStyle: CSSProperties = {
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  color: '#64748b',
  marginBottom: 6,
};

const metricValueStyle: CSSProperties = {
  fontWeight: 700,
  color: '#0f172a',
  wordBreak: 'break-word',
};

const tableStyle: CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
};

const thStyle: CSSProperties = {
  textAlign: 'left',
  padding: '10px 8px',
  borderBottom: '1px solid #e2e8f0',
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  color: '#64748b',
};

const tdStyle: CSSProperties = {
  padding: '10px 8px',
  borderBottom: '1px solid #e2e8f0',
  verticalAlign: 'top',
};

const panelStyle: CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 14,
  padding: 14,
  background: '#fff',
};

const panelHeadingStyle: CSSProperties = {
  marginTop: 0,
  marginBottom: 10,
};

const subpanelGridStyle: CSSProperties = {
  display: 'grid',
  gap: 12,
  marginTop: 16,
};

const listStyle: CSSProperties = {
  margin: '12px 0 0',
  paddingLeft: 18,
  color: '#475569',
  lineHeight: 1.7,
};
