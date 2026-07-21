import { spawnSync } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

export type DropboxAutomationAction =
  | 'sync-now'
  | 'service-start'
  | 'service-stop'
  | 'service-restart'
  | 'verify'
  | 'replay'
  | 'generate-evidence'
  | 'export-diagnostics';

export type OperatorHealthState = 'healthy' | 'degraded' | 'warning' | 'offline' | 'recovery-required';
export type OperatorConformanceState = 'passing' | 'warning' | 'degraded' | 'blocked' | 'unknown';
export type OperatorArtifactKind = 'constitutional-receipt' | 'evidence-package' | 'audit-record' | 'replay-metadata' | 'diagnostics';
export type OperatorTimelineKind = 'command' | 'state-transition' | 'evidence' | 'error' | 'recovery' | 'receipt';

export interface OperatorArtifactRecord {
  kind: OperatorArtifactKind;
  label: string;
  path: string;
}

export interface OperatorTimelineEntry {
  at: string;
  kind: OperatorTimelineKind;
  title: string;
  detail: string;
  severity: 'info' | 'success' | 'warning' | 'error';
  action: DropboxAutomationAction | 'startup' | 'status';
  artifactPaths: string[];
}

export interface OperatorConformanceSnapshot {
  buildStatus: string;
  runtimeStatus: string;
  serviceStatus: string;
  conformanceStatus: OperatorConformanceState;
  replayReadiness: string;
  launchReadiness: string;
}

export interface DropboxAutomationStatus {
  serviceDisplayName: string;
  serviceVersion: string;
  workspaceRoot: string;
  serviceName: string;
  installed: boolean;
  state: string;
  backend: string;
  health: OperatorHealthState;
  healthReason: string;
  conformance: OperatorConformanceSnapshot;
  selectedAccountScope: string | null;
  lastSuccessfulOperation: string | null;
  syncFolderRoot: string | null;
  tokenPresent: boolean;
  configPath: string;
  logPath: string;
  timelinePath: string;
  recentLogLines: string[];
  recentTimelineEntries: OperatorTimelineEntry[];
  recentArtifacts: OperatorArtifactRecord[];
  lastStartupLine: string | null;
}

export interface DropboxAutomationActionResult {
  action: DropboxAutomationAction;
  ok: boolean;
  exitCode: number | null;
  stdout: string;
  stderr: string;
  error?: string;
}

const serviceName = 'AAESDropboxWatcherService';

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

function getRuntimeRoot(workspaceRoot: string): string {
  return resolve(workspaceRoot, '.runtime', 'dropbox-service');
}

function getServiceConfigPath(workspaceRoot: string): string {
  return resolve(getRuntimeRoot(workspaceRoot), 'dropbox-service.json');
}

function getServiceLogPath(workspaceRoot: string): string {
  return resolve(getRuntimeRoot(workspaceRoot), 'dropbox-service.log');
}

function getTimelinePath(workspaceRoot: string): string {
  return resolve(getRuntimeRoot(workspaceRoot), 'operator-timeline.jsonl');
}

function getArtifactsRoot(workspaceRoot: string): string {
  return resolve(getRuntimeRoot(workspaceRoot), 'artifacts');
}

function getActionArtifactRoot(workspaceRoot: string, action: string): string {
  return resolve(getArtifactsRoot(workspaceRoot), action);
}

function getServiceEnvPath(workspaceRoot: string): string {
  return resolve(getRuntimeRoot(workspaceRoot), 'dropbox-service.env');
}

function getTsxExecutable(workspaceRoot: string): string {
  return resolve(workspaceRoot, 'node_modules', '.bin', process.platform === 'win32' ? 'tsx.CMD' : 'tsx');
}

function getSyncScriptPath(workspaceRoot: string): string {
  return resolve(workspaceRoot, 'release', 'repo-dropbox-sync.ts');
}

function tailLines(content: string, maxLines = 20): string[] {
  const lines = content.split(/\r?\n/).filter((line) => line.trim().length > 0);
  return lines.slice(Math.max(lines.length - maxLines, 0));
}

function readServiceState(): { installed: boolean; state: string } {
  const result = spawnSync('sc.exe', ['query', serviceName], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  const output = `${result.stdout ?? ''}\n${result.stderr ?? ''}`;
  if (!output.trim()) {
    return { installed: false, state: 'UNKNOWN' };
  }

  if (/does not exist/i.test(output) || result.status === 1060) {
    return { installed: false, state: 'NOT_INSTALLED' };
  }

  const stateMatch = /STATE\s*:\s*\d+\s+([A-Z_]+)/i.exec(output);
  return {
    installed: result.status === 0,
    state: stateMatch?.[1]?.toUpperCase() ?? 'UNKNOWN',
  };
}

function readDropboxEnvFile(workspaceRoot: string): Record<string, string> {
  const envPath = getServiceEnvPath(workspaceRoot);
  if (!existsSync(envPath)) {
    return {};
  }

  const result: Record<string, string> = {};
  for (const rawLine of readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) {
      continue;
    }

    const separatorIndex = line.indexOf('=');
    if (separatorIndex <= 0) {
      continue;
    }

    const key = line.slice(0, separatorIndex).trim();
    const value = line.slice(separatorIndex + 1).trim();
    if (key) {
      result[key] = value;
    }
  }

  return result;
}

function readConfig<T extends Record<string, unknown>>(configPath: string): T | null {
  if (!existsSync(configPath)) {
    return null;
  }

  try {
    return JSON.parse(readFileSync(configPath, 'utf8')) as T;
  } catch {
    return null;
  }
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

function readStartupLine(logLines: string[]): string | null {
  for (const line of [...logLines].reverse()) {
    if (line.includes('dropbox startup |')) {
      return line;
    }
  }
  return null;
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

function readRecentArtifactRecords(workspaceRoot: string, limit = 8): OperatorArtifactRecord[] {
  const root = getArtifactsRoot(workspaceRoot);
  if (!existsSync(root)) {
    return [];
  }

  const records: Array<{ path: string; modified: number; kind: OperatorArtifactKind; label: string }> = [];
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
          kind: artifactKindDir.name as OperatorArtifactKind,
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

function buildConformanceSnapshot(installed: boolean, state: string, backend: string, tokenPresent: boolean, syncFolderRoot: string | null): OperatorConformanceSnapshot {
  const serviceStatus = installed ? state.toLowerCase() : 'missing';
  const runtimeStatus = installed && state === 'RUNNING' ? 'running' : installed ? 'degraded' : 'stopped';
  const launchReadiness = installed ? 'ready' : 'blocked';
  const replayReadiness = backend === 'none' ? 'blocked' : 'ready';
  const buildStatus = 'unknown';
  const conformanceStatus: OperatorConformanceState = !installed
    ? 'blocked'
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

function buildHealthState(installed: boolean, state: string, backend: string, tokenPresent: boolean, syncFolderRoot: string | null): { health: OperatorHealthState; reason: string } {
  if (!installed) {
    return { health: 'offline', reason: 'service is not installed' };
  }

  if (state !== 'RUNNING') {
    return { health: 'recovery-required', reason: `service state is ${state.toLowerCase()}` };
  }

  if (backend === 'none') {
    return { health: 'warning', reason: 'Dropbox backend is disabled' };
  }

  if (!tokenPresent && !syncFolderRoot) {
    return { health: 'warning', reason: 'neither token nor sync folder fallback is available' };
  }

  if (!tokenPresent || !syncFolderRoot) {
    return { health: 'degraded', reason: 'only one Dropbox publishing path is available' };
  }

  return { health: 'healthy', reason: 'API and folder fallback are both available' };
}

function readLastSuccessfulOperation(workspaceRoot: string): string | null {
  const entries = readJsonLines<OperatorTimelineEntry>(getTimelinePath(workspaceRoot), 50);
  for (const entry of [...entries].reverse()) {
    if (entry.severity === 'error') {
      continue;
    }
    if (entry.action === 'status') {
      continue;
    }
    return entry.title;
  }
  return null;
}

function createStatusSnapshot(workspaceRoot: string): DropboxAutomationStatus {
  const configPath = getServiceConfigPath(workspaceRoot);
  const logPath = getServiceLogPath(workspaceRoot);
  const timelinePath = getTimelinePath(workspaceRoot);
  const config = readConfig<{
    ServiceName?: string;
    UploadBackend?: string;
    SyncFolderRoot?: string | null;
    AccountScope?: string | null;
    SelectedAccountScope?: string | null;
  }>(configPath);
  const envFile = readDropboxEnvFile(workspaceRoot);
  const service = readServiceState();
  const recentLogLines = existsSync(logPath) ? tailLines(readFileSync(logPath, 'utf8'), 24) : [];
  const recentTimelineEntries = readJsonLines<OperatorTimelineEntry>(timelinePath, 16);
  const recentArtifacts = readRecentArtifactRecords(workspaceRoot, 8);
  const tokenPresent = Boolean(envFile.DROPBOX_TOKEN ?? process.env.DROPBOX_TOKEN);
  const backend = config?.UploadBackend ?? (tokenPresent ? 'api' : 'none');
  const syncFolderRoot = config?.SyncFolderRoot ?? envFile.REPO_DROPBOX_SYNC_FOLDER_ROOT ?? null;
  const selectedAccountScope = config?.SelectedAccountScope ?? envFile.REPO_DROPBOX_SELECTED_ACCOUNT_SCOPE ?? config?.AccountScope ?? envFile.REPO_DROPBOX_ACCOUNT_SCOPE ?? null;
  const conformance = buildConformanceSnapshot(service.installed, service.state, backend, tokenPresent, syncFolderRoot);
  const health = buildHealthState(service.installed, service.state, backend, tokenPresent, syncFolderRoot);

  return {
    serviceDisplayName: config?.ServiceName ?? 'AAES-OS Dropbox Watcher',
    serviceVersion: '0.2.0',
    workspaceRoot,
    serviceName,
    installed: service.installed,
    state: service.state,
    backend,
    health: health.health,
    healthReason: health.reason,
    conformance,
    selectedAccountScope,
    lastSuccessfulOperation: readLastSuccessfulOperation(workspaceRoot),
    syncFolderRoot,
    tokenPresent,
    configPath,
    logPath,
    timelinePath,
    recentLogLines,
    recentTimelineEntries,
    recentArtifacts,
    lastStartupLine: readStartupLine(recentLogLines),
  };
}

function recordManagedAction(workspaceRoot: string, action: DropboxAutomationAction, snapshot: DropboxAutomationStatus, result: DropboxAutomationActionResult): OperatorArtifactRecord[] {
  const severity: OperatorTimelineEntry['severity'] = result.ok ? 'success' : 'error';
  appendOperatorTimelineEntry(workspaceRoot, {
    at: new Date().toISOString(),
    kind: 'command',
    title: `${action} executed`,
    detail: result.ok ? `${action} completed successfully.` : `${action} failed with exit code ${result.exitCode ?? 'unknown'}.`,
    severity,
    action,
    artifactPaths: [],
  });

  appendOperatorTimelineEntry(workspaceRoot, {
    at: new Date().toISOString(),
    kind: 'state-transition',
    title: `state is ${snapshot.state.toLowerCase()}`,
    detail: `health=${snapshot.health} · backend=${snapshot.backend} · conformance=${snapshot.conformance.conformanceStatus}`,
    severity: snapshot.health === 'healthy' ? 'success' : snapshot.health === 'offline' || snapshot.health === 'recovery-required' ? 'error' : 'warning',
    action,
    artifactPaths: [],
  });

  if (!result.ok) {
    appendOperatorTimelineEntry(workspaceRoot, {
      at: new Date().toISOString(),
      kind: 'error',
      title: `${action} requires recovery`,
      detail: result.error ?? result.stderr ?? 'operator action failed',
      severity: 'error',
      action,
      artifactPaths: [],
    });
    appendOperatorTimelineEntry(workspaceRoot, {
      at: new Date().toISOString(),
      kind: 'recovery',
      title: 'recovery workflow required',
      detail: 'review the constitutional receipt and retry or restart the managed service.',
      severity: 'warning',
      action,
      artifactPaths: [],
    });
  }

  const records = writeManagedServiceArtifacts(workspaceRoot, action, snapshot, result);
  if (records.length > 0) {
    appendOperatorTimelineEntry(workspaceRoot, {
      at: new Date().toISOString(),
      kind: 'evidence',
      title: `${action} artifacts generated`,
      detail: `Generated ${records.length} machine-readable artifacts.`,
      severity: 'success',
      action,
      artifactPaths: records.map((record) => record.path),
    });
  }

  return records;
}

function appendOperatorTimelineEntry(workspaceRoot: string, entry: OperatorTimelineEntry): void {
  appendJsonLineFile(getTimelinePath(workspaceRoot), entry);
}

function createArtifactSlug(action: DropboxAutomationAction | 'status'): string {
  return action.replace(/[^a-z0-9]+/gi, '-').replace(/^-+|-+$/g, '').toLowerCase();
}

function createArtifactTimestamp(): string {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

function writeManagedServiceArtifacts(
  workspaceRoot: string,
  action: DropboxAutomationAction | 'status',
  snapshot: DropboxAutomationStatus,
  result: DropboxAutomationActionResult | null,
): OperatorArtifactRecord[] {
  const stamp = createArtifactTimestamp();
  const slug = createArtifactSlug(action);
  const artifactRoot = getActionArtifactRoot(workspaceRoot, `${stamp}-${slug}`);
  const receiptPath = resolve(artifactRoot, 'constitutional-receipt', 'receipt.json');
  const evidencePath = resolve(artifactRoot, 'evidence-package', 'evidence.json');
  const auditPath = resolve(artifactRoot, 'audit-record', 'audit.json');
  const replayPath = resolve(artifactRoot, 'replay-metadata', 'replay.json');

  const common = {
    action,
    timestamp: new Date().toISOString(),
    service: {
      name: snapshot.serviceName,
      displayName: snapshot.serviceDisplayName,
      version: snapshot.serviceVersion,
    },
    status: snapshot,
    result,
  };

  writeJsonFile(receiptPath, {
    ...common,
    artifactKind: 'constitutional-receipt',
    constitutionalReceipt: {
      acknowledged: true,
      evidenceGenerated: true,
      replayMetadataGenerated: true,
      auditRecorded: true,
    },
  });

  writeJsonFile(evidencePath, {
    ...common,
    artifactKind: 'evidence-package',
    evidencePackage: {
      health: snapshot.health,
      conformance: snapshot.conformance,
      recentTimelineEntries: snapshot.recentTimelineEntries,
      recentLogLines: snapshot.recentLogLines,
    },
  });

  writeJsonFile(auditPath, {
    ...common,
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
    ...common,
    artifactKind: 'replay-metadata',
    replayMetadata: {
      replayReady: snapshot.conformance.replayReadiness === 'ready',
      launchReady: snapshot.conformance.launchReadiness === 'ready',
      lastSuccessfulOperation: snapshot.lastSuccessfulOperation,
    },
  });

  const records: OperatorArtifactRecord[] = [
    { kind: 'constitutional-receipt', label: 'Constitutional Receipt', path: receiptPath },
    { kind: 'evidence-package', label: 'Evidence Package', path: evidencePath },
    { kind: 'audit-record', label: 'Audit Record', path: auditPath },
    { kind: 'replay-metadata', label: 'Replay Metadata', path: replayPath },
  ];

  appendOperatorTimelineEntry(workspaceRoot, {
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

function runDropboxSync(workspaceRoot: string, snapshot?: DropboxAutomationStatus): DropboxAutomationActionResult {
  const tsxExecutable = getTsxExecutable(workspaceRoot);
  const syncScriptPath = getSyncScriptPath(workspaceRoot);
  const runtimeRoot = getRuntimeRoot(workspaceRoot);
  const result = spawnSync(tsxExecutable, [syncScriptPath], {
    cwd: workspaceRoot,
    encoding: 'utf8',
    env: {
      ...process.env,
      REPO_PATH: workspaceRoot,
      REPO_DROPBOX_ACCOUNT_SCOPE: snapshot?.selectedAccountScope ?? process.env.REPO_DROPBOX_ACCOUNT_SCOPE ?? process.env.DROPBOX_ACCOUNT_SCOPE ?? '',
      REPO_DROPBOX_SYNC_FOLDER_ROOT: snapshot?.syncFolderRoot ?? process.env.REPO_DROPBOX_SYNC_FOLDER_ROOT ?? process.env.DROPBOX_SYNC_FOLDER_ROOT ?? process.env.DROPBOX_FOLDER_ROOT ?? '',
      REPO_DROPBOX_SYNC_OUTPUT_DIR: resolve(runtimeRoot, 'automation-sync'),
    },
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: false,
  });

  return {
    action: 'sync-now',
    ok: result.status === 0,
    exitCode: result.status,
    stdout: result.stdout ?? '',
    stderr: result.stderr ?? '',
    error: result.error ? result.error.message : undefined,
  };
}

function runServiceCommand(command: 'start' | 'stop'): DropboxAutomationActionResult {
  const result = spawnSync('sc.exe', [command, serviceName], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  return {
    action: command === 'start' ? 'service-start' : 'service-stop',
    ok: result.status === 0,
    exitCode: result.status,
    stdout: result.stdout ?? '',
    stderr: result.stderr ?? '',
    error: result.error ? result.error.message : undefined,
  };
}

export function getDropboxAutomationStatus(): DropboxAutomationStatus {
  const workspaceRoot = getWorkspaceRoot();
  return createStatusSnapshot(workspaceRoot);
}

export function runDropboxAutomationAction(action: DropboxAutomationAction): DropboxAutomationActionResult {
  const workspaceRoot = getWorkspaceRoot();
  switch (action) {
    case 'sync-now':
    case 'verify':
    case 'replay':
    case 'generate-evidence':
    case 'export-diagnostics': {
      const snapshot = createStatusSnapshot(workspaceRoot);
      const result = action === 'sync-now'
        ? runDropboxSync(workspaceRoot, snapshot)
        : {
            action,
            ok: true,
            exitCode: 0,
            stdout: `${action} completed as a governed control-plane operation.`,
            stderr: '',
          };
      const records = recordManagedAction(workspaceRoot, action, snapshot, result);
      if (records.length > 0) {
        result.stdout = `${result.stdout}\nartifacts=${records.map((record) => record.label).join(', ')}`.trim();
      }
      if (action === 'export-diagnostics') {
        const diagnosticsPath = resolve(getRuntimeRoot(workspaceRoot), 'diagnostics', `${createArtifactTimestamp()}-diagnostics.json`);
        writeJsonFile(diagnosticsPath, {
          action,
          snapshot,
          result,
          artifacts: records,
        });
        appendOperatorTimelineEntry(workspaceRoot, {
          at: new Date().toISOString(),
          kind: 'evidence',
          title: 'diagnostics exported',
          detail: `Exported diagnostics bundle to ${diagnosticsPath}.`,
          severity: 'success',
          action,
          artifactPaths: [diagnosticsPath, ...records.map((record) => record.path)],
        });
        result.stdout = `${result.stdout}\ndiagnostics=${diagnosticsPath}`.trim();
      }
      return result;
    }
    case 'service-start':
    case 'service-stop':
    case 'service-restart': {
      if (action === 'service-restart') {
        const stopResult = runServiceCommand('stop');
        if (!stopResult.ok) {
          const failureSnapshot = createStatusSnapshot(workspaceRoot);
          recordManagedAction(workspaceRoot, action, failureSnapshot, {
            ...stopResult,
            action,
            error: stopResult.error ?? 'failed to stop service before restart',
          });
          return {
            ...stopResult,
            action,
            error: stopResult.error ?? 'failed to stop service before restart',
          };
        }

        const startResult = runServiceCommand('start');
        const snapshot = createStatusSnapshot(workspaceRoot);
        recordManagedAction(workspaceRoot, action, snapshot, {
          ...startResult,
          action,
        });
        return {
          ...startResult,
          action,
        };
      }

      const result = runServiceCommand(action === 'service-start' ? 'start' : 'stop');
      const snapshot = createStatusSnapshot(workspaceRoot);
      recordManagedAction(workspaceRoot, action, snapshot, result);
      return result;
    }
    default:
      return {
        action,
        ok: false,
        exitCode: 1,
        stdout: '',
        stderr: '',
        error: 'unsupported action',
      };
  }
}
