#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export type ExternalIntegrationStatus = 'verified' | 'blocked';

export interface ExternalIntegrationObservation {
  id: string;
  service: 'GitHub' | 'npm Registry';
  target: string;
  mode: string;
  status: ExternalIntegrationStatus;
  checkedAt: string;
  evidenceHash: string;
  command?: string;
  endpoint?: string;
  observed: Record<string, string | number | boolean | null>;
  blockers: string[];
}

export interface ExternalIntegrationEvidenceIndex {
  generatedAt: string;
  workspace: string;
  status: ExternalIntegrationStatus;
  observations: ExternalIntegrationObservation[];
  aggregateHash: string;
}

interface BuildOptions {
  root?: string;
  outputDir?: string;
  now?: Date;
  write?: boolean;
}

const defaultRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export async function buildExternalIntegrationEvidence(options: BuildOptions = {}): Promise<ExternalIntegrationEvidenceIndex> {
  const root = options.root ?? defaultRoot;
  const outputDir = options.outputDir ?? path.join(root, 'docs', 'release', 'external-integrations');
  const checkedAt = (options.now ?? new Date()).toISOString();
  const observations = [
    probeGitHubRemote(root, checkedAt),
    await probeNpmRegistry(root, checkedAt),
  ];
  const aggregateHash = hashJson(observations.map((observation) => ({ id: observation.id, status: observation.status, evidenceHash: observation.evidenceHash })));
  const index: ExternalIntegrationEvidenceIndex = {
    generatedAt: checkedAt,
    workspace: normalizePath(root),
    status: observations.every((observation) => observation.status === 'verified') ? 'verified' : 'blocked',
    observations,
    aggregateHash,
  };

  if (options.write ?? true) {
    writeEvidenceFiles(outputDir, index);
  }

  return index;
}

export function summarizeExternalIntegrationEvidence(index: ExternalIntegrationEvidenceIndex): {
  verifiedCount: number;
  blockedCount: number;
  services: string[];
} {
  const verifiedCount = index.observations.filter((observation) => observation.status === 'verified').length;
  const blockedCount = index.observations.length - verifiedCount;
  return {
    verifiedCount,
    blockedCount,
    services: [...new Set(index.observations.map((observation) => observation.service))].sort(),
  };
}

export function isExternalIntegrationEvidenceIndex(value: unknown): value is ExternalIntegrationEvidenceIndex {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const index = value as Partial<ExternalIntegrationEvidenceIndex>;
  return (
    isNonEmptyString(index.generatedAt) &&
    isNonEmptyString(index.workspace) &&
    (index.status === 'verified' || index.status === 'blocked') &&
    isNonEmptyString(index.aggregateHash) &&
    Array.isArray(index.observations) &&
    index.observations.every(isExternalIntegrationObservation)
  );
}

function probeGitHubRemote(root: string, checkedAt: string): ExternalIntegrationObservation {
  const command = 'git ls-remote origin HEAD';
  const errors: string[] = [];
  try {
    const output = execGitWithRetry(root, ['ls-remote', 'origin', 'HEAD'], 3, 30000, errors).trim();
    const [commit, ref] = output.split(/\s+/);
    const remoteUrl = execGitWithRetry(root, ['remote', 'get-url', 'origin'], 1, 5000, errors).trim();
    const blockers = isSha(commit) && ref === 'HEAD' ? [] : ['GitHub origin HEAD did not return a valid commit/ref pair'];
    return buildObservation({
      id: 'github-origin-remote',
      service: 'GitHub',
      target: remoteUrl,
      mode: 'git-ls-remote',
      checkedAt,
      command,
      observed: {
        remote: remoteUrl,
        ref,
        commit,
        attempts: errors.length + 1,
      },
      blockers,
    });
  } catch (error) {
    return buildObservation({
      id: 'github-origin-remote',
      service: 'GitHub',
      target: 'origin',
      mode: 'git-ls-remote',
      checkedAt,
      command,
      observed: {
        error: error instanceof Error ? error.message : String(error),
        attempts: errors.length,
        transientErrors: errors.join(' | '),
      },
      blockers: ['GitHub origin remote could not be reached'],
    });
  }
}

async function probeNpmRegistry(root: string, checkedAt: string): Promise<ExternalIntegrationObservation> {
  const packageJson = readWorkspacePackageJson(root);
  const packageManager = typeof packageJson.packageManager === 'string' ? packageJson.packageManager : 'pnpm';
  const packageName = packageManager.split('@')[0] || 'pnpm';
  const endpoint = `https://registry.npmjs.org/${encodeURIComponent(packageName)}`;

  try {
    const errors: string[] = [];
    const response = await fetchWithRetry(endpoint, 3, 30000, errors);
    const payload = (await response.json()) as unknown;
    const observedName = readStringField(payload, 'name');
    const latest = readNestedStringField(payload, ['dist-tags', 'latest']);
    const blockers = [
      response.ok ? '' : `npm registry responded with HTTP ${response.status}`,
      observedName === packageName ? '' : 'npm registry payload name mismatch',
      latest ? '' : 'npm registry payload is missing dist-tags.latest',
    ].filter(Boolean);
    return buildObservation({
      id: 'npm-registry-toolchain',
      service: 'npm Registry',
      target: packageName,
      mode: 'registry-metadata-fetch',
      checkedAt,
      endpoint,
      observed: {
        requestedPackage: packageName,
        workspacePackageManager: packageManager,
        httpStatus: response.status,
        registryName: observedName,
        latestVersion: latest,
        attempts: errors.length + 1,
      },
      blockers,
    });
  } catch (error) {
    return buildObservation({
      id: 'npm-registry-toolchain',
      service: 'npm Registry',
      target: packageName,
      mode: 'registry-metadata-fetch',
      checkedAt,
      endpoint,
      observed: {
        requestedPackage: packageName,
        workspacePackageManager: packageManager,
        error: error instanceof Error ? error.message : String(error),
      },
      blockers: ['npm registry metadata could not be fetched'],
    });
  }
}

function execGitWithRetry(root: string, args: string[], attempts: number, timeoutMs: number, errors: string[]): string {
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return execFileSync('git', args, {
        cwd: root,
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: timeoutMs,
      });
    } catch (error) {
      errors.push(error instanceof Error ? error.message : String(error));
      if (attempt === attempts) {
        throw error;
      }
    }
  }

  throw new Error('unreachable git retry state');
}

async function fetchWithRetry(url: string, attempts: number, timeoutMs: number, errors: string[]): Promise<Response> {
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return await fetchWithTimeout(url, timeoutMs);
    } catch (error) {
      errors.push(error instanceof Error ? error.message : String(error));
      if (attempt === attempts) {
        throw error;
      }
    }
  }

  throw new Error('unreachable fetch retry state');
}

function buildObservation(input: Omit<ExternalIntegrationObservation, 'status' | 'evidenceHash'>): ExternalIntegrationObservation {
  const status: ExternalIntegrationStatus = input.blockers.length === 0 ? 'verified' : 'blocked';
  const evidenceHash = hashJson({ ...input, status });
  return {
    ...input,
    status,
    evidenceHash,
  };
}

function writeEvidenceFiles(outputDir: string, index: ExternalIntegrationEvidenceIndex): void {
  mkdirSync(outputDir, { recursive: true });
  writeFileSync(path.join(outputDir, 'external-integration-index.json'), `${JSON.stringify(index, null, 2)}\n`, 'utf8');
  writeFileSync(path.join(outputDir, 'README.md'), `${renderMarkdown(index)}\n`, 'utf8');
}

function renderMarkdown(index: ExternalIntegrationEvidenceIndex): string {
  const lines = [
    '# External Integration Evidence',
    '',
    `Generated: ${index.generatedAt}`,
    '',
    `Status: \`${index.status}\``,
    '',
    `Aggregate hash: \`${index.aggregateHash}\``,
    '',
    '| Service | Target | Mode | Status | Evidence hash |',
    '| --- | --- | --- | --- | --- |',
    ...index.observations.map((observation) => `| ${observation.service} | ${observation.target} | ${observation.mode} | ${observation.status} | ${observation.evidenceHash} |`),
    '',
    'This packet records read-only, real-service probes used by the production-hardening release evidence. It does not write to external systems.',
  ];

  return lines.join('\n');
}

function readWorkspacePackageJson(root: string): { packageManager?: unknown } {
  const packageJsonPath = path.join(root, 'package.json');
  if (!existsSync(packageJsonPath)) {
    return {};
  }
  return JSON.parse(readFileSync(packageJsonPath, 'utf8')) as { packageManager?: unknown };
}

function isExternalIntegrationObservation(value: unknown): value is ExternalIntegrationObservation {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const observation = value as Partial<ExternalIntegrationObservation>;
  return (
    isNonEmptyString(observation.id) &&
    (observation.service === 'GitHub' || observation.service === 'npm Registry') &&
    isNonEmptyString(observation.target) &&
    isNonEmptyString(observation.mode) &&
    (observation.status === 'verified' || observation.status === 'blocked') &&
    isNonEmptyString(observation.checkedAt) &&
    isNonEmptyString(observation.evidenceHash) &&
    typeof observation.observed === 'object' &&
    observation.observed !== null &&
    Array.isArray(observation.blockers) &&
    observation.blockers.every((blocker) => typeof blocker === 'string')
  );
}

async function fetchWithTimeout(url: string, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, {
      headers: {
        'User-Agent': 'aaes-os-production-hardening-evidence/1.0',
      },
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

function readStringField(value: unknown, key: string): string | null {
  if (typeof value !== 'object' || value === null) {
    return null;
  }
  const field = (value as Record<string, unknown>)[key];
  return typeof field === 'string' && field.trim().length > 0 ? field : null;
}

function readNestedStringField(value: unknown, keys: string[]): string | null {
  let current = value;
  for (const key of keys) {
    if (typeof current !== 'object' || current === null) {
      return null;
    }
    current = (current as Record<string, unknown>)[key];
  }
  return typeof current === 'string' && current.trim().length > 0 ? current : null;
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function isSha(value: unknown): value is string {
  return typeof value === 'string' && /^[a-f0-9]{40,64}$/i.test(value);
}

function hashJson(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(stableValue(value))).digest('hex');
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(stableValue);
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, entry]) => [key, stableValue(entry)]),
    );
  }
  return value;
}

function normalizePath(filePath: string): string {
  return filePath.replace(/\\/g, '/');
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  buildExternalIntegrationEvidence()
    .then((index) => {
      if (index.status === 'blocked') {
        throw new Error(`external integration evidence blocked for: ${index.observations.filter((observation) => observation.status === 'blocked').map((observation) => observation.id).join(', ')}`);
      }
      console.log(`external integration evidence generated: ${index.observations.length} services`);
      console.log(`aggregate hash: ${index.aggregateHash}`);
    })
    .catch((error: unknown) => {
      console.error(error instanceof Error ? error.message : String(error));
      process.exitCode = 1;
    });
}
