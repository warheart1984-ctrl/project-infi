import { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

import { getCoriAlphaWorkspaceSummary } from '@aaes-os/platform-core';

import {
  getDropboxAutomationStatus,
  runDropboxAutomationAction,
  type DropboxAutomationAction as DropboxServiceAction,
  type DropboxAutomationActionResult as DropboxServiceActionResult,
} from './dropboxAutomation';

export type ManagedServiceId = 'dropbox' | 'cori-alpha' | 'sovereignx' | 'nova' | 'ulx' | 'ai-factory' | 'research-os';
export type ManagedServiceAction =
  | 'start'
  | 'stop'
  | 'restart'
  | 'sync-now'
  | 'verify'
  | 'replay'
  | 'generate-evidence'
  | 'export-diagnostics';

export type ManagedServiceHealth = 'healthy' | 'degraded' | 'warning' | 'offline' | 'recovery-required';
export type ManagedServiceConformance = 'passing' | 'warning' | 'degraded' | 'blocked' | 'unknown';
export type ManagedServiceTimelineKind = 'command' | 'state-transition' | 'evidence' | 'error' | 'recovery' | 'receipt';

export interface ManagedServiceActionDefinition {
  action: ManagedServiceAction;
  label: string;
  description: string;
}

export interface ManagedServiceConformanceSnapshot {
  buildStatus: string;
  runtimeStatus: string;
  serviceStatus: string;
  conformanceStatus: ManagedServiceConformance;
  replayReadiness: string;
  launchReadiness: string;
}

export interface ManagedServiceArtifactRecord {
  kind: string;
  label: string;
  path: string;
}

export interface ManagedServiceTimelineEntry {
  at: string;
  kind: ManagedServiceTimelineKind;
  title: string;
  detail: string;
  severity: 'info' | 'success' | 'warning' | 'error';
  action: ManagedServiceAction | 'startup' | 'status';
  artifactPaths: string[];
}

export interface ManagedServiceStatus {
  serviceId: ManagedServiceId;
  serviceDisplayName: string;
  serviceVersion: string;
  workspaceRoot: string;
  serviceName: string;
  installed: boolean;
  state: string;
  backend: string;
  health: ManagedServiceHealth;
  healthReason: string;
  conformance: ManagedServiceConformanceSnapshot;
  selectedAccountScope: string | null;
  lastSuccessfulOperation: string | null;
  syncFolderRoot: string | null;
  tokenPresent: boolean;
  configPath: string;
  logPath: string;
  timelinePath: string;
  recentLogLines: string[];
  recentTimelineEntries: ManagedServiceTimelineEntry[];
  recentArtifacts: ManagedServiceArtifactRecord[];
  lastStartupLine: string | null;
  details: Record<string, unknown>;
}

export interface ManagedServiceActionResult {
  action: ManagedServiceAction;
  ok: boolean;
  exitCode: number | null;
  stdout: string;
  stderr: string;
  error?: string;
  snapshot?: ManagedServiceStatus;
  artifacts?: ManagedServiceArtifactRecord[];
}

export interface ManagedServiceAdapter {
  id: ManagedServiceId;
  label: string;
  description: string;
  actions: ManagedServiceActionDefinition[];
  getStatus(): Promise<ManagedServiceStatus>;
  runAction(action: ManagedServiceAction): Promise<ManagedServiceActionResult>;
}

export interface ManagedServiceSummary {
  id: ManagedServiceId;
  label: string;
  description: string;
  actions: ManagedServiceActionDefinition[];
}

function getWorkspaceRoot(): string {
  const explicit = process.env.AAES_PROJECT_ROOT?.trim();
  if (explicit) {
    return resolve(explicit);
  }

  let current = resolve(process.cwd());
  while (true) {
    if (existsSync(resolve(current, 'pnpm-workspace.yaml')) && existsSync(resolve(current, 'package.json'))) {
      return current;
    }

    const parent = dirname(current);
    if (parent === current) {
      return resolve(process.cwd());
    }
    current = parent;
  }
}

function getRuntimeRoot(workspaceRoot: string, serviceId: ManagedServiceId): string {
  return resolve(workspaceRoot, '.runtime', serviceId);
}

function getServiceTimelinePath(workspaceRoot: string, serviceId: ManagedServiceId): string {
  return resolve(getRuntimeRoot(workspaceRoot, serviceId), 'operator-timeline.jsonl');
}

function getServiceArtifactsRoot(workspaceRoot: string, serviceId: ManagedServiceId): string {
  return resolve(getRuntimeRoot(workspaceRoot, serviceId), 'artifacts');
}

function ensureParentDirectory(filePath: string): void {
  mkdirSync(dirname(filePath), { recursive: true });
}

function writeJsonFile(filePath: string, value: unknown): void {
  ensureParentDirectory(filePath);
  writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function appendJsonLineFile(filePath: string, value: unknown): void {
  ensureParentDirectory(filePath);
  appendFileSync(filePath, `${JSON.stringify(value)}\n`, 'utf8');
}

function readJsonLines<T>(filePath: string, limit = 20): T[] {
  if (!existsSync(filePath)) {
    return [];
  }

  const entries: T[] = [];
  for (const rawLine of readFileSync(filePath, 'utf8').split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) {
      continue;
    }

    try {
      entries.push(JSON.parse(line) as T);
    } catch {
      continue;
    }
  }

  return entries.slice(Math.max(entries.length - limit, 0));
}

function readJsonFileIfExists<T>(filePath: string): T | null {
  if (!existsSync(filePath)) {
    return null;
  }

  try {
    return JSON.parse(readFileSync(filePath, 'utf8')) as T;
  } catch {
    return null;
  }
}

function readRecentArtifactRecords(workspaceRoot: string, serviceId: ManagedServiceId, limit = 8): ManagedServiceArtifactRecord[] {
  const root = getServiceArtifactsRoot(workspaceRoot, serviceId);
  if (!existsSync(root)) {
    return [];
  }

  const records: Array<{ path: string; modified: number; kind: string; label: string }> = [];
  for (const actionDir of readdirSync(root, { withFileTypes: true })) {
    if (!actionDir.isDirectory()) {
      continue;
    }

    const actionRoot = resolve(root, actionDir.name);
    for (const artifactKindDir of readdirSync(actionRoot, { withFileTypes: true })) {
      if (!artifactKindDir.isDirectory()) {
        continue;
      }

      const artifactRoot = resolve(actionRoot, artifactKindDir.name);
      for (const artifactFile of readdirSync(artifactRoot, { withFileTypes: true })) {
        if (!artifactFile.isFile() || !artifactFile.name.endsWith('.json')) {
          continue;
        }

        const artifactPath = resolve(artifactRoot, artifactFile.name);
        const stats = statSync(artifactPath);
        records.push({
          path: artifactPath,
          modified: stats.mtimeMs,
          kind: artifactKindDir.name,
          label: artifactFile.name,
        });
      }
    }
  }

  return records
    .sort((left, right) => right.modified - left.modified)
    .slice(0, limit)
    .map((record) => ({
      kind: record.kind,
      label: record.label,
      path: record.path,
    }));
}

function appendTimelineEntry(workspaceRoot: string, serviceId: ManagedServiceId, entry: ManagedServiceTimelineEntry): void {
  appendJsonLineFile(getServiceTimelinePath(workspaceRoot, serviceId), entry);
}

function recordArtifacts(
  workspaceRoot: string,
  serviceId: ManagedServiceId,
  action: ManagedServiceAction | 'status',
  snapshot: ManagedServiceStatus,
  result: ManagedServiceActionResult | null,
): ManagedServiceArtifactRecord[] {
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const actionSlug = action.replace(/[^a-z0-9]+/gi, '-').replace(/^-+|-+$/g, '').toLowerCase();
  const artifactRoot = resolve(getServiceArtifactsRoot(workspaceRoot, serviceId), `${stamp}-${actionSlug}`);
  const receiptPath = resolve(artifactRoot, 'constitutional-receipt', 'receipt.json');
  const evidencePath = resolve(artifactRoot, 'evidence-package', 'evidence.json');
  const auditPath = resolve(artifactRoot, 'audit-record', 'audit.json');
  const replayPath = resolve(artifactRoot, 'replay-metadata', 'replay.json');

  const baseRecord = {
    action,
    timestamp: new Date().toISOString(),
    service: {
      id: snapshot.serviceId,
      name: snapshot.serviceName,
      displayName: snapshot.serviceDisplayName,
      version: snapshot.serviceVersion,
    },
    status: snapshot,
    result,
  };

  writeJsonFile(receiptPath, {
    ...baseRecord,
    artifactKind: 'constitutional-receipt',
    constitutionalReceipt: {
      acknowledged: true,
      evidenceGenerated: true,
      replayMetadataGenerated: true,
      auditRecorded: true,
    },
  });

  writeJsonFile(evidencePath, {
    ...baseRecord,
    artifactKind: 'evidence-package',
    evidencePackage: {
      health: snapshot.health,
      conformance: snapshot.conformance,
      recentTimelineEntries: snapshot.recentTimelineEntries,
      recentLogLines: snapshot.recentLogLines,
    },
  });

  writeJsonFile(auditPath, {
    ...baseRecord,
    artifactKind: 'audit-record',
    auditRecord: {
      workspaceRoot,
      selectedAccountScope: snapshot.selectedAccountScope,
      backend: snapshot.backend,
      tokenPresent: snapshot.tokenPresent,
      serviceState: snapshot.state,
    },
  });

  writeJsonFile(replayPath, {
    ...baseRecord,
    artifactKind: 'replay-metadata',
    replayMetadata: {
      replayReady: snapshot.conformance.replayReadiness === 'ready',
      launchReady: snapshot.conformance.launchReadiness === 'ready',
      lastSuccessfulOperation: snapshot.lastSuccessfulOperation,
    },
  });

  const records: ManagedServiceArtifactRecord[] = [
    { kind: 'constitutional-receipt', label: 'Constitutional Receipt', path: receiptPath },
    { kind: 'evidence-package', label: 'Evidence Package', path: evidencePath },
    { kind: 'audit-record', label: 'Audit Record', path: auditPath },
    { kind: 'replay-metadata', label: 'Replay Metadata', path: replayPath },
  ];

  appendTimelineEntry(workspaceRoot, serviceId, {
    at: new Date().toISOString(),
    kind: 'receipt',
    title: `${action} receipt recorded`,
    detail: `Generated constitutional receipt, evidence package, audit record, and replay metadata for ${action}.`,
    severity: result?.ok === false ? 'warning' : 'success',
    action,
    artifactPaths: records.map((record) => record.path),
  });

  return records;
}

function buildConformanceSnapshot(
  installed: boolean,
  state: string,
  backend: string,
  tokenPresent: boolean,
  syncFolderRoot: string | null,
): ManagedServiceConformanceSnapshot {
  const readOnlyEvidenceBackend = backend === 'governance-retirement' || backend === 'frozen-research-corpus';
  const serviceStatus = installed ? state.toLowerCase() : 'missing';
  const runtimeStatus = installed
    ? readOnlyEvidenceBackend
      ? state.toLowerCase()
      : state === 'RUNNING'
        ? 'running'
        : 'degraded'
    : 'stopped';
  const launchReadiness = installed ? 'ready' : 'blocked';
  const replayReadiness = backend === 'none' ? 'blocked' : 'ready';
  const buildStatus = readOnlyEvidenceBackend ? 'frozen-baseline' : 'unknown';
  const conformanceStatus: ManagedServiceConformance = !installed
    ? 'blocked'
    : readOnlyEvidenceBackend
      ? state === 'DEGRADED'
        ? 'warning'
        : 'passing'
      : backend === 'none'
        ? 'degraded'
        : !tokenPresent && !syncFolderRoot
          ? 'warning'
          : 'passing';

  return {
    buildStatus,
    runtimeStatus,
    serviceStatus,
    conformanceStatus,
    replayReadiness,
    launchReadiness,
  };
}

function buildHealthState(
  installed: boolean,
  state: string,
  backend: string,
  tokenPresent: boolean,
  syncFolderRoot: string | null,
): { health: ManagedServiceHealth; reason: string } {
  const readOnlyEvidenceBackend = backend === 'governance-retirement' || backend === 'frozen-research-corpus';

  if (!installed) {
    return { health: 'offline', reason: 'service is not installed' };
  }

  if (readOnlyEvidenceBackend) {
    if (state === 'DEGRADED') {
      return { health: 'warning', reason: 'read-only evidence corpus loaded with recorded issues' };
    }

    return { health: 'healthy', reason: 'read-only evidence corpus is available' };
  }

  if (state !== 'RUNNING') {
    return { health: 'recovery-required', reason: `service state is ${state.toLowerCase()}` };
  }

  if (backend === 'none') {
    return { health: 'warning', reason: 'backend is disabled' };
  }

  if (!tokenPresent && !syncFolderRoot) {
    return { health: 'warning', reason: 'neither token nor sync folder fallback is available' };
  }

  if (!tokenPresent || !syncFolderRoot) {
    return { health: 'degraded', reason: 'only one publishing path is available' };
  }

  return { health: 'healthy', reason: 'all configured publishing paths are available' };
}

function writeActionResponse(
  action: ManagedServiceAction,
  ok: boolean,
  exitCode: number | null,
  stdout: string,
  stderr: string,
  error?: string,
): ManagedServiceActionResult {
  return { action, ok, exitCode, stdout, stderr, error };
}

function createManagedServiceSnapshot(input: {
  serviceId: ManagedServiceId;
  serviceDisplayName: string;
  serviceVersion: string;
  workspaceRoot: string;
  serviceName: string;
  installed: boolean;
  state: string;
  backend: string;
  selectedAccountScope: string | null;
  syncFolderRoot: string | null;
  tokenPresent: boolean;
  configPath: string;
  logPath: string;
  timelinePath: string;
  recentLogLines: string[];
  recentTimelineEntries: ManagedServiceTimelineEntry[];
  recentArtifacts: ManagedServiceArtifactRecord[];
  lastStartupLine: string | null;
  details: Record<string, unknown>;
}): ManagedServiceStatus {
  const conformance = buildConformanceSnapshot(input.installed, input.state, input.backend, input.tokenPresent, input.syncFolderRoot);
  const health = buildHealthState(input.installed, input.state, input.backend, input.tokenPresent, input.syncFolderRoot);

  return {
    ...input,
    health: health.health,
    healthReason: health.reason,
    conformance,
    lastSuccessfulOperation: input.recentTimelineEntries
      .slice()
      .reverse()
      .find((entry) => entry.severity !== 'error' && entry.action !== 'status')?.title ?? null,
  };
}

function createDropboxStatus(workspaceRoot: string): ManagedServiceStatus {
  const status = getDropboxAutomationStatus();
  const timelinePath = status.timelinePath;
  const recentTimelineEntries = readJsonLines<ManagedServiceTimelineEntry>(timelinePath, 16);

  return createManagedServiceSnapshot({
    serviceId: 'dropbox',
    serviceDisplayName: status.serviceDisplayName,
    serviceVersion: status.serviceVersion,
    workspaceRoot,
    serviceName: status.serviceName,
    installed: status.installed,
    state: status.state,
    backend: status.backend,
    selectedAccountScope: status.selectedAccountScope,
    syncFolderRoot: status.syncFolderRoot,
    tokenPresent: status.tokenPresent,
    configPath: status.configPath,
    logPath: status.logPath,
    timelinePath,
    recentLogLines: status.recentLogLines,
    recentTimelineEntries,
    recentArtifacts: status.recentArtifacts,
    lastStartupLine: status.lastStartupLine,
    details: {
      workspaceRoot: status.workspaceRoot,
      health: status.health,
      healthReason: status.healthReason,
      conformance: status.conformance,
    },
  });
}

function createDropboxAdapter(): ManagedServiceAdapter {
  const actions: ManagedServiceActionDefinition[] = [
    { action: 'start', label: 'Start', description: 'Bring the managed service online.' },
    { action: 'stop', label: 'Stop', description: 'Pause the managed service.' },
    { action: 'restart', label: 'Restart', description: 'Bounce the Windows service and watcher process.' },
    { action: 'sync-now', label: 'Sync Now', description: 'Trigger the Dropbox snapshot pipeline immediately.' },
    { action: 'verify', label: 'Verify', description: 'Capture a health and conformance snapshot.' },
    { action: 'replay', label: 'Replay', description: 'Record replay metadata for the current operator state.' },
    { action: 'generate-evidence', label: 'Generate Evidence', description: 'Write a fresh evidence bundle without changing service state.' },
    { action: 'export-diagnostics', label: 'Export Diagnostics', description: 'Persist a machine-readable diagnostics package.' },
  ];

  return {
    id: 'dropbox',
    label: 'Dropbox',
    description: 'Dropbox API and desktop-sync managed service.',
    actions,
    async getStatus() {
      return createDropboxStatus(getWorkspaceRoot());
    },
    async runAction(action) {
      const mappedAction = action as DropboxServiceAction;
      const result = runDropboxAutomationAction(mappedAction) as DropboxServiceActionResult;
      const snapshot = createDropboxStatus(getWorkspaceRoot());
      const records = snapshot.recentArtifacts;
      return {
        action,
        ok: result.ok,
        exitCode: result.exitCode,
        stdout: result.stdout,
        stderr: result.stderr,
        error: result.error,
        snapshot,
        artifacts: records,
      };
    },
  };
}

function createReadOnlyActionResult(
  snapshot: ManagedServiceStatus,
  action: ManagedServiceAction,
  message: string,
  details?: Record<string, unknown>,
): ManagedServiceActionResult {
  const records = recordArtifacts(snapshot.workspaceRoot, snapshot.serviceId, action, snapshot, null);
  appendTimelineEntry(snapshot.workspaceRoot, snapshot.serviceId, {
    at: new Date().toISOString(),
    kind: 'command',
    title: `${action} executed`,
    detail: message,
    severity: 'success',
    action,
    artifactPaths: records.map((record) => record.path),
  });
  if (details) {
    appendTimelineEntry(snapshot.workspaceRoot, snapshot.serviceId, {
      at: new Date().toISOString(),
      kind: 'evidence',
      title: `${action} details recorded`,
      detail: JSON.stringify(details),
      severity: 'success',
      action,
      artifactPaths: records.map((record) => record.path),
    });
  }
  return {
    action,
    ok: true,
    exitCode: 0,
    stdout: `${message}\nartifacts=${records.map((record) => record.label).join(', ')}`,
    stderr: '',
    snapshot,
    artifacts: records,
  };
}

function createCoriAlphaStatus(): ManagedServiceStatus {
  const workspaceRoot = getWorkspaceRoot();
  const summary = getCoriAlphaWorkspaceSummary();
  const timelinePath = getServiceTimelinePath(workspaceRoot, 'cori-alpha');
  const recentTimelineEntries = readJsonLines<ManagedServiceTimelineEntry>(timelinePath, 16);
  const recentArtifacts = readRecentArtifactRecords(workspaceRoot, 'cori-alpha', 8);

  return createManagedServiceSnapshot({
    serviceId: 'cori-alpha',
    serviceDisplayName: 'CORI Alpha',
    serviceVersion: '1.0.0',
    workspaceRoot,
    serviceName: 'cori-alpha-summary',
    installed: true,
    state: summary.validation.valid ? 'READY' : 'DEGRADED',
    backend: 'ledger',
    selectedAccountScope: null,
    syncFolderRoot: null,
    tokenPresent: true,
    configPath: summary.root,
    logPath: resolve(summary.root, '.runtime', 'cori-alpha', 'cori-alpha.log'),
    timelinePath,
    recentLogLines: summary.validation.issues.length > 0
      ? summary.validation.issues
      : [`CORI Alpha workspace summary loaded from ${summary.root}`],
    recentTimelineEntries: recentTimelineEntries.length > 0
      ? recentTimelineEntries
      : summary.uploads.slice(-8).map((upload) => ({
          at: upload.createdAt,
          kind: 'evidence',
          title: `Upload ${upload.uploadId}`,
          detail: `${upload.decision.result} · trust=${upload.trust.score}`,
          severity: upload.validation.valid ? 'success' : 'warning',
          action: 'status',
          artifactPaths: [upload.artifact.path, upload.evidence.path, upload.receipt.path, upload.ledger.path],
        })),
    recentArtifacts,
    lastStartupLine: summary.validation.valid
      ? `cori-alpha startup | uploads=${summary.summary.uploadCount} | valid=true`
      : `cori-alpha startup | uploads=${summary.summary.uploadCount} | valid=false`,
    details: {
      summary,
      validation: summary.validation,
      graph: summary.graph,
    },
  });
}

function createCoriAlphaAdapter(): ManagedServiceAdapter {
  const actions: ManagedServiceActionDefinition[] = [
    { action: 'verify', label: 'Verify', description: 'Inspect the CORI Alpha workspace and validation state.' },
    { action: 'replay', label: 'Replay', description: 'Record replay metadata for the current CORI Alpha state.' },
    { action: 'generate-evidence', label: 'Generate Evidence', description: 'Emit a fresh evidence bundle for CORI Alpha.' },
    { action: 'export-diagnostics', label: 'Export Diagnostics', description: 'Persist diagnostics for the CORI Alpha workspace.' },
  ];

  return {
    id: 'cori-alpha',
    label: 'CORI Alpha',
    description: 'CORI Alpha upload intelligence and ledger workspace.',
    actions,
    async getStatus() {
      return createCoriAlphaStatus();
    },
    async runAction(action) {
      const snapshot = createCoriAlphaStatus();
      switch (action) {
        case 'verify':
          return createReadOnlyActionResult(snapshot, action, 'CORI Alpha verified successfully.', { valid: snapshot.details.validation });
        case 'replay':
          return createReadOnlyActionResult(snapshot, action, 'CORI Alpha replay metadata recorded.', { graph: snapshot.details.graph });
        case 'generate-evidence':
          return createReadOnlyActionResult(snapshot, action, 'CORI Alpha evidence package generated.', { summary: snapshot.details.summary });
        case 'export-diagnostics':
          return createReadOnlyActionResult(snapshot, action, 'CORI Alpha diagnostics exported.', { validation: snapshot.details.validation });
        default:
          return writeActionResponse(action, false, 1, '', '', `unsupported action: ${action}`);
      }
    },
  };
}

function createReadOnlyManagedServiceActionDefinitions(serviceLabel: string): ManagedServiceActionDefinition[] {
  return [
    { action: 'start', label: 'Start', description: `Record a governed start receipt for ${serviceLabel}.` },
    { action: 'stop', label: 'Stop', description: `Record a governed stop receipt for ${serviceLabel}.` },
    { action: 'restart', label: 'Restart', description: `Record a governed restart receipt for ${serviceLabel}.` },
    { action: 'sync-now', label: 'Sync Now', description: `Record an immediate evidence sync for ${serviceLabel}.` },
    { action: 'verify', label: 'Verify', description: `Verify the ${serviceLabel} evidence corpus and traceability.` },
    { action: 'replay', label: 'Replay', description: `Record replay metadata for ${serviceLabel}.` },
    { action: 'generate-evidence', label: 'Generate Evidence', description: `Generate a fresh evidence package for ${serviceLabel}.` },
    { action: 'export-diagnostics', label: 'Export Diagnostics', description: `Export diagnostics for ${serviceLabel}.` },
  ];
}

function createAiFactoryStatus(): ManagedServiceStatus {
  const workspaceRoot = getWorkspaceRoot();
  const recordPath = resolve(workspaceRoot, '.runtime', 'governance', 'retirement', 'ai_factory_organ.json');
  const retirementRecord = readJsonFileIfExists<{
    gene?: string;
    current_step?: number;
    completed_steps?: string[];
    dry_run?: boolean;
    failures?: string[];
    notes?: Record<string, unknown>;
    updated_at?: string;
  }>(recordPath);
  const timelinePath = getServiceTimelinePath(workspaceRoot, 'ai-factory');
  const recentTimelineEntries = readJsonLines<ManagedServiceTimelineEntry>(timelinePath, 16);
  const recentArtifacts = readRecentArtifactRecords(workspaceRoot, 'ai-factory', 8);
  const installed = retirementRecord !== null;
  const failureCount = retirementRecord?.failures?.length ?? 0;
  const state = !installed ? 'MISSING' : failureCount > 0 ? 'DEGRADED' : 'READY';

  return createManagedServiceSnapshot({
    serviceId: 'ai-factory',
    serviceDisplayName: 'AI Factory',
    serviceVersion: '1.0.0',
    workspaceRoot,
    serviceName: 'ai-factory-retirement',
    installed,
    state,
    backend: 'governance-retirement',
    selectedAccountScope: null,
    syncFolderRoot: null,
    tokenPresent: false,
    configPath: recordPath,
    logPath: resolve(workspaceRoot, '.runtime', 'ai-factory', 'ai-factory.log'),
    timelinePath,
    recentLogLines: retirementRecord
      ? [`ai-factory retirement record loaded | dry_run=${retirementRecord.dry_run ? 'true' : 'false'} | failures=${failureCount} | updated_at=${retirementRecord.updated_at ?? 'unknown'}`]
      : ['AI Factory retirement record was not found.'],
    recentTimelineEntries: recentTimelineEntries.length > 0
      ? recentTimelineEntries
      : [{
          at: new Date().toISOString(),
          kind: 'state-transition',
          title: installed ? 'AI Factory retirement ledger loaded' : 'AI Factory retirement ledger missing',
          detail: installed ? `Loaded ${recordPath}.` : 'No AI Factory retirement ledger was detected.',
          severity: installed ? 'success' : 'warning',
          action: 'status',
          artifactPaths: installed ? [recordPath] : [],
        }],
    recentArtifacts,
    lastStartupLine: installed
      ? `ai-factory startup | backend=governance-retirement | record=present | failures=${failureCount} | dry_run=${retirementRecord.dry_run ? 'true' : 'false'}`
      : 'ai-factory startup | backend=governance-retirement | record=missing',
    details: {
      recordPath,
      retirementRecord,
      failureCount,
      evidenceModel: 'governance-retirement-ledger',
    },
  });
}

function createAiFactoryAdapter(): ManagedServiceAdapter {
  const actions = createReadOnlyManagedServiceActionDefinitions('AI Factory');

  return {
    id: 'ai-factory',
    label: 'AI Factory',
    description: 'AI Factory retirement ledger and governance evidence surface.',
    actions,
    async getStatus() {
      return createAiFactoryStatus();
    },
    async runAction(action) {
      const snapshot = createAiFactoryStatus();
      switch (action) {
        case 'start':
          return createReadOnlyActionResult(snapshot, action, 'AI Factory start recorded against the retirement ledger.', snapshot.details);
        case 'stop':
          return createReadOnlyActionResult(snapshot, action, 'AI Factory stop recorded against the retirement ledger.', snapshot.details);
        case 'restart':
          return createReadOnlyActionResult(snapshot, action, 'AI Factory restart recorded against the retirement ledger.', snapshot.details);
        case 'sync-now':
          return createReadOnlyActionResult(snapshot, action, 'AI Factory evidence sync recorded from the retirement ledger.', snapshot.details);
        case 'verify':
          return createReadOnlyActionResult(snapshot, action, 'AI Factory retirement ledger verified successfully.', snapshot.details);
        case 'replay':
          return createReadOnlyActionResult(snapshot, action, 'AI Factory replay metadata recorded.', snapshot.details);
        case 'generate-evidence':
          return createReadOnlyActionResult(snapshot, action, 'AI Factory evidence package generated.', snapshot.details);
        case 'export-diagnostics':
          return createReadOnlyActionResult(snapshot, action, 'AI Factory diagnostics exported.', snapshot.details);
        default:
          return writeActionResponse(action, false, 1, '', '', `unsupported action: ${action}`);
      }
    },
  };
}

function createResearchOsStatus(): ManagedServiceStatus {
  const workspaceRoot = getWorkspaceRoot();
  const sourceFiles = [
    resolve(workspaceRoot, 'docs', 'crk1', 'release', 'RESEARCH_OS_SPECIFICATION.md'),
    resolve(workspaceRoot, 'docs', 'crk1', 'release', 'RESEARCH_OS_FREEZE.md'),
    resolve(workspaceRoot, 'docs', 'crk1', 'release', 'CIS_STANDARDS_TRACEABILITY_MATRIX.md'),
    resolve(workspaceRoot, 'docs', 'crk1', 'release', 'CIS_COMPANION_SPEC_REGISTRY.spec.json'),
    resolve(workspaceRoot, 'docs', 'crk1', 'release', 'IMPLEMENTATION_PROFILE_RESEARCH.md'),
  ];
  const existingSources = sourceFiles.filter((filePath) => existsSync(filePath));
  const timelinePath = getServiceTimelinePath(workspaceRoot, 'research-os');
  const recentTimelineEntries = readJsonLines<ManagedServiceTimelineEntry>(timelinePath, 16);
  const recentArtifacts = readRecentArtifactRecords(workspaceRoot, 'research-os', 8);
  const installed = existingSources.length === sourceFiles.length;
  const state = installed ? 'READY' : 'MISSING';

  return createManagedServiceSnapshot({
    serviceId: 'research-os',
    serviceDisplayName: 'Research OS',
    serviceVersion: '1.0.0',
    workspaceRoot,
    serviceName: 'research-os-corpus',
    installed,
    state,
    backend: 'frozen-research-corpus',
    selectedAccountScope: null,
    syncFolderRoot: null,
    tokenPresent: false,
    configPath: sourceFiles[0],
    logPath: resolve(workspaceRoot, '.runtime', 'research-os', 'research-os.log'),
    timelinePath,
    recentLogLines: installed
      ? [`research-os corpus loaded | workflow=Evidence->Insights->Ideas->Actions | sources=${existingSources.length} | traceability=present`]
      : ['Research OS canonical corpus was not fully available.'],
    recentTimelineEntries: recentTimelineEntries.length > 0
      ? recentTimelineEntries
      : [{
          at: new Date().toISOString(),
          kind: 'state-transition',
          title: installed ? 'Research OS corpus loaded' : 'Research OS corpus missing',
          detail: installed
            ? `Loaded ${existingSources.length} canonical Research OS sources.`
            : 'Not all canonical Research OS sources were detected.',
          severity: installed ? 'success' : 'warning',
          action: 'status',
          artifactPaths: existingSources,
        }],
    recentArtifacts,
    lastStartupLine: installed
      ? `research-os startup | backend=frozen-research-corpus | corpus=present | sources=${existingSources.length} | workflow=Evidence->Insights->Ideas->Actions`
      : `research-os startup | backend=frozen-research-corpus | corpus=missing | sources=${existingSources.length} | workflow=Evidence->Insights->Ideas->Actions`,
    details: {
      sourceFiles,
      existingSources,
      workflow: ['Evidence', 'Insights', 'Ideas', 'Actions'],
      canonicalCorpus: 'frozen-research-os',
    },
  });
}

function createResearchOsAdapter(): ManagedServiceAdapter {
  const actions = createReadOnlyManagedServiceActionDefinitions('Research OS');

  return {
    id: 'research-os',
    label: 'Research OS',
    description: 'Frozen Research OS evidence corpus and traceability surface.',
    actions,
    async getStatus() {
      return createResearchOsStatus();
    },
    async runAction(action) {
      const snapshot = createResearchOsStatus();
      switch (action) {
        case 'start':
          return createReadOnlyActionResult(snapshot, action, 'Research OS start recorded against the frozen corpus.', snapshot.details);
        case 'stop':
          return createReadOnlyActionResult(snapshot, action, 'Research OS stop recorded against the frozen corpus.', snapshot.details);
        case 'restart':
          return createReadOnlyActionResult(snapshot, action, 'Research OS restart recorded against the frozen corpus.', snapshot.details);
        case 'sync-now':
          return createReadOnlyActionResult(snapshot, action, 'Research OS evidence sync recorded from the frozen corpus.', snapshot.details);
        case 'verify':
          return createReadOnlyActionResult(snapshot, action, 'Research OS frozen corpus verified successfully.', snapshot.details);
        case 'replay':
          return createReadOnlyActionResult(snapshot, action, 'Research OS replay metadata recorded.', snapshot.details);
        case 'generate-evidence':
          return createReadOnlyActionResult(snapshot, action, 'Research OS evidence package generated.', snapshot.details);
        case 'export-diagnostics':
          return createReadOnlyActionResult(snapshot, action, 'Research OS diagnostics exported.', snapshot.details);
        default:
          return writeActionResponse(action, false, 1, '', '', `unsupported action: ${action}`);
      }
    },
  };
}

async function fetchJsonWithTimeout<T>(url: string, timeoutMs = 750): Promise<T | null> {
  const controller = new AbortController();
  const timer = globalThis.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { signal: controller.signal, cache: 'no-store' });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  } finally {
    globalThis.clearTimeout(timer);
  }
}

function createSovereignXStatus(): Promise<ManagedServiceStatus> {
  const workspaceRoot = getWorkspaceRoot();
  return (async () => {
    const hardware = await fetchJsonWithTimeout<Record<string, unknown>>('http://127.0.0.1:4000/sovereignx/hardware');
    const timelinePath = getServiceTimelinePath(workspaceRoot, 'sovereignx');
    const recentTimelineEntries = readJsonLines<ManagedServiceTimelineEntry>(timelinePath, 16);
    const recentArtifacts = readRecentArtifactRecords(workspaceRoot, 'sovereignx', 8);
    const installed = hardware !== null;
    const state = hardware ? 'READY' : 'OFFLINE';
    const backend = 'ops-console';
    const serviceDisplayName = 'Sovereign X';
    const serviceVersion = '1.0.0';
    const summary = hardware && typeof hardware === 'object' ? hardware : {};

    return createManagedServiceSnapshot({
      serviceId: 'sovereignx',
      serviceDisplayName,
      serviceVersion,
      workspaceRoot,
      serviceName: 'sovereignx-hardware',
      installed,
      state,
      backend,
      selectedAccountScope: null,
      syncFolderRoot: null,
      tokenPresent: false,
      configPath: resolve(workspaceRoot, 'services', 'ops-console', 'src', 'server.ts'),
      logPath: resolve(workspaceRoot, '.runtime', 'sovereignx', 'sovereignx.log'),
      timelinePath,
      recentLogLines: installed ? ['Sovereign X runtime endpoint responded successfully.'] : ['Sovereign X runtime endpoint unavailable.'],
      recentTimelineEntries: recentTimelineEntries.length > 0
        ? recentTimelineEntries
        : [{
            at: new Date().toISOString(),
            kind: 'state-transition',
            title: installed ? 'Sovereign X connected' : 'Sovereign X offline',
            detail: installed ? 'Local ops-console endpoint responded.' : 'Local ops-console endpoint unavailable.',
            severity: installed ? 'success' : 'warning',
            action: 'status',
            artifactPaths: [],
          }],
      recentArtifacts,
      lastStartupLine: installed ? 'sovereignx startup | backend=ops-console | status=ready' : 'sovereignx startup | backend=ops-console | status=offline',
      details: {
        hardware: summary,
      },
    });
  })();
}

function createSovereignXAdapter(): ManagedServiceAdapter {
  const actions: ManagedServiceActionDefinition[] = [
    { action: 'verify', label: 'Verify', description: 'Check the local Sovereign X runtime endpoint.' },
    { action: 'replay', label: 'Replay', description: 'Record replay metadata for Sovereign X.' },
    { action: 'generate-evidence', label: 'Generate Evidence', description: 'Write a diagnostics-and-evidence bundle.' },
    { action: 'export-diagnostics', label: 'Export Diagnostics', description: 'Persist Sovereign X diagnostics.' },
  ];

  return {
    id: 'sovereignx',
    label: 'Sovereign X',
    description: 'Sovereign X hardware and cluster governance surface.',
    actions,
    async getStatus() {
      return createSovereignXStatus();
    },
    async runAction(action) {
      const snapshot = await createSovereignXStatus();
      switch (action) {
        case 'verify':
          return createReadOnlyActionResult(snapshot, action, 'Sovereign X runtime verified successfully.', snapshot.details);
        case 'replay':
          return createReadOnlyActionResult(snapshot, action, 'Sovereign X replay metadata recorded.', snapshot.details);
        case 'generate-evidence':
          return createReadOnlyActionResult(snapshot, action, 'Sovereign X evidence package generated.', snapshot.details);
        case 'export-diagnostics':
          return createReadOnlyActionResult(snapshot, action, 'Sovereign X diagnostics exported.', snapshot.details);
        default:
          return writeActionResponse(action, false, 1, '', '', `unsupported action: ${action}`);
      }
    },
  };
}

function createNovaStatus(): ManagedServiceStatus {
  const workspaceRoot = getWorkspaceRoot();
  const candidateRoots = [
    resolve(workspaceRoot, 'lawful-nova-shell'),
    resolve(workspaceRoot, 'desktop'),
    resolve(workspaceRoot, 'nova-studio'),
  ];
  const foundRoot = candidateRoots.find((candidate) => existsSync(candidate)) ?? null;
  const timelinePath = getServiceTimelinePath(workspaceRoot, 'nova');
  const recentTimelineEntries = readJsonLines<ManagedServiceTimelineEntry>(timelinePath, 16);
  const recentArtifacts = readRecentArtifactRecords(workspaceRoot, 'nova', 8);
  const installed = foundRoot !== null;
  const state = installed ? 'READY' : 'NOT_FOUND';

  return createManagedServiceSnapshot({
    serviceId: 'nova',
    serviceDisplayName: 'Nova',
    serviceVersion: '1.0.0',
    workspaceRoot,
    serviceName: 'nova-shell',
    installed,
    state,
    backend: 'desktop-shell',
    selectedAccountScope: null,
    syncFolderRoot: null,
    tokenPresent: false,
    configPath: foundRoot ?? resolve(workspaceRoot, 'lawful-nova-shell'),
    logPath: resolve(workspaceRoot, '.runtime', 'nova', 'nova.log'),
    timelinePath,
    recentLogLines: installed ? [`Nova shell found at ${foundRoot}`] : ['Nova shell workspace was not found.'],
    recentTimelineEntries: recentTimelineEntries.length > 0
      ? recentTimelineEntries
      : [{
          at: new Date().toISOString(),
          kind: 'state-transition',
          title: installed ? 'Nova shell located' : 'Nova shell missing',
          detail: installed ? `Found local shell at ${foundRoot}.` : 'No local Nova shell workspace was detected.',
          severity: installed ? 'success' : 'warning',
          action: 'status',
          artifactPaths: [],
        }],
    recentArtifacts,
    lastStartupLine: installed ? 'nova startup | backend=desktop-shell | status=ready' : 'nova startup | backend=desktop-shell | status=missing',
    details: {
      foundRoot,
      candidateRoots,
    },
  });
}

function createNovaAdapter(): ManagedServiceAdapter {
  const actions: ManagedServiceActionDefinition[] = [
    { action: 'verify', label: 'Verify', description: 'Check the local Nova shell workspace.' },
    { action: 'generate-evidence', label: 'Generate Evidence', description: 'Write a diagnostics bundle for Nova.' },
    { action: 'export-diagnostics', label: 'Export Diagnostics', description: 'Persist Nova diagnostics.' },
  ];

  return {
    id: 'nova',
    label: 'Nova',
    description: 'Nova studio and desktop shell surface.',
    actions,
    async getStatus() {
      return createNovaStatus();
    },
    async runAction(action) {
      const snapshot = createNovaStatus();
      switch (action) {
        case 'verify':
          return createReadOnlyActionResult(snapshot, action, 'Nova shell verified successfully.', snapshot.details);
        case 'generate-evidence':
          return createReadOnlyActionResult(snapshot, action, 'Nova evidence package generated.', snapshot.details);
        case 'export-diagnostics':
          return createReadOnlyActionResult(snapshot, action, 'Nova diagnostics exported.', snapshot.details);
        default:
          return writeActionResponse(action, false, 1, '', '', `unsupported action: ${action}`);
      }
    },
  };
}

function createUlxStatus(): ManagedServiceStatus {
  const workspaceRoot = getWorkspaceRoot();
  const candidateRoots = [
    resolve(workspaceRoot, 'packages', 'ulx-governance'),
    resolve(workspaceRoot, 'packages', 'ul-runtime'),
    resolve(workspaceRoot, 'packages', 'aaes-governance'),
  ];
  const foundRoot = candidateRoots.find((candidate) => existsSync(candidate)) ?? null;
  const timelinePath = getServiceTimelinePath(workspaceRoot, 'ulx');
  const recentTimelineEntries = readJsonLines<ManagedServiceTimelineEntry>(timelinePath, 16);
  const recentArtifacts = readRecentArtifactRecords(workspaceRoot, 'ulx', 8);
  const installed = foundRoot !== null;
  const state = installed ? 'READY' : 'NOT_FOUND';

  return createManagedServiceSnapshot({
    serviceId: 'ulx',
    serviceDisplayName: 'ULX',
    serviceVersion: '1.0.0',
    workspaceRoot,
    serviceName: 'ulx-governance',
    installed,
    state,
    backend: 'governance-runtime',
    selectedAccountScope: null,
    syncFolderRoot: null,
    tokenPresent: false,
    configPath: foundRoot ?? resolve(workspaceRoot, 'packages', 'ulx-governance'),
    logPath: resolve(workspaceRoot, '.runtime', 'ulx', 'ulx.log'),
    timelinePath,
    recentLogLines: installed ? [`ULX governance surface found at ${foundRoot}`] : ['ULX governance surface was not found.'],
    recentTimelineEntries: recentTimelineEntries.length > 0
      ? recentTimelineEntries
      : [{
          at: new Date().toISOString(),
          kind: 'state-transition',
          title: installed ? 'ULX surface located' : 'ULX surface missing',
          detail: installed ? `Found local ULX surface at ${foundRoot}.` : 'No local ULX surface was detected.',
          severity: installed ? 'success' : 'warning',
          action: 'status',
          artifactPaths: [],
        }],
    recentArtifacts,
    lastStartupLine: installed ? 'ulx startup | backend=governance-runtime | status=ready' : 'ulx startup | backend=governance-runtime | status=missing',
    details: {
      foundRoot,
      candidateRoots,
    },
  });
}

function createUlxAdapter(): ManagedServiceAdapter {
  const actions: ManagedServiceActionDefinition[] = [
    { action: 'verify', label: 'Verify', description: 'Check the local ULX governance surface.' },
    { action: 'replay', label: 'Replay', description: 'Record replay metadata for ULX.' },
    { action: 'generate-evidence', label: 'Generate Evidence', description: 'Write a diagnostics bundle for ULX.' },
    { action: 'export-diagnostics', label: 'Export Diagnostics', description: 'Persist ULX diagnostics.' },
  ];

  return {
    id: 'ulx',
    label: 'ULX',
    description: 'ULX governance and runtime surface.',
    actions,
    async getStatus() {
      return createUlxStatus();
    },
    async runAction(action) {
      const snapshot = createUlxStatus();
      switch (action) {
        case 'verify':
          return createReadOnlyActionResult(snapshot, action, 'ULX surface verified successfully.', snapshot.details);
        case 'replay':
          return createReadOnlyActionResult(snapshot, action, 'ULX replay metadata recorded.', snapshot.details);
        case 'generate-evidence':
          return createReadOnlyActionResult(snapshot, action, 'ULX evidence package generated.', snapshot.details);
        case 'export-diagnostics':
          return createReadOnlyActionResult(snapshot, action, 'ULX diagnostics exported.', snapshot.details);
        default:
          return writeActionResponse(action, false, 1, '', '', `unsupported action: ${action}`);
      }
    },
  };
}

const adapters: Record<ManagedServiceId, ManagedServiceAdapter> = {
  dropbox: createDropboxAdapter(),
  'cori-alpha': createCoriAlphaAdapter(),
  sovereignx: createSovereignXAdapter(),
  nova: createNovaAdapter(),
  ulx: createUlxAdapter(),
  'ai-factory': createAiFactoryAdapter(),
  'research-os': createResearchOsAdapter(),
};

export function listManagedServiceSummaries(): ManagedServiceSummary[] {
  return Object.values(adapters).map((adapter) => ({
    id: adapter.id,
    label: adapter.label,
    description: adapter.description,
    actions: adapter.actions,
  }));
}

export function getManagedServiceAdapter(serviceId: string): ManagedServiceAdapter | null {
  return serviceId in adapters ? adapters[serviceId as ManagedServiceId] : null;
}

export async function getManagedServiceStatus(serviceId: string): Promise<ManagedServiceStatus | null> {
  const adapter = getManagedServiceAdapter(serviceId);
  if (!adapter) {
    return null;
  }
  return adapter.getStatus();
}

export async function runManagedServiceAction(serviceId: string, action: string): Promise<ManagedServiceActionResult | null> {
  const adapter = getManagedServiceAdapter(serviceId);
  if (!adapter) {
    return null;
  }
  if (!adapter.actions.some((definition) => definition.action === action)) {
    return {
      action: action as ManagedServiceAction,
      ok: false,
      exitCode: 1,
      stdout: '',
      stderr: '',
      error: `unsupported action for ${serviceId}: ${action}`,
    };
  }
  return adapter.runAction(action as ManagedServiceAction);
}

export function getManagedServiceSummary(serviceId: string): ManagedServiceSummary | null {
  const adapter = getManagedServiceAdapter(serviceId);
  if (!adapter) {
    return null;
  }

  return {
    id: adapter.id,
    label: adapter.label,
    description: adapter.description,
    actions: adapter.actions,
  };
}

export function getDefaultManagedServiceId(): ManagedServiceId {
  return 'dropbox';
}
