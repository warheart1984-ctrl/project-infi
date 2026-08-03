import {
  applySovereignXClusterControlRequest,
  getSovereignXClusterControlState,
  replaceSovereignXClusterControlState,
  resetSovereignXClusterControlState,
  type SovereignXClusterControlRequest,
  type SovereignXClusterControlState,
} from './sovereignxClusterGovernance.js';

export type SovereignXClusterControlOutcome = 'applied' | 'noop' | 'rejected' | 'remote-applied' | 'remote-fallback';

export type SovereignXClusterControlAuditEntry = {
  auditId: string;
  requestedAtMs: number;
  action: SovereignXClusterControlRequest['action'];
  nodeId: string | null;
  reason: string;
  outcome: SovereignXClusterControlOutcome;
  backend: 'local' | 'remote';
  detail: string;
};

export type SovereignXClusterControlAdapterResult = {
  outcome: SovereignXClusterControlOutcome;
  controlState: SovereignXClusterControlState;
  auditEntry: SovereignXClusterControlAuditEntry;
};

export interface SovereignXClusterControlAdapter {
  readonly backend: 'local' | 'remote';
  readonly controlUrl: string | null;
  applyControl(request: SovereignXClusterControlRequest, observedAtMs: number): Promise<SovereignXClusterControlAdapterResult>;
  auditTrail(): SovereignXClusterControlAuditEntry[];
  status(): { backend: 'local' | 'remote'; controlUrl: string | null; auditEntryCount: number };
}

export type SovereignXClusterControlAdapterOptions = {
  controlUrl?: string;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
};

function defaultReason(request: SovereignXClusterControlRequest): string {
  return request.reason?.trim() || `cluster control ${(request.action ?? 'steady_state').replace('_', ' ')}`;
}

function toAuditId(observedAtMs: number): string {
  return `svx-control-${observedAtMs.toString(16)}-${Math.random().toString(16).slice(2, 10)}`;
}

function isControlState(value: unknown): value is SovereignXClusterControlState {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    typeof record.desiredNodeCount === 'number' &&
    Array.isArray(record.quarantinedNodeIds) &&
    record.quarantinedNodeIds.every((entry) => typeof entry === 'string')
  );
}

class SovereignXLocalClusterControlAdapter implements SovereignXClusterControlAdapter {
  readonly backend = 'local' as const;
  readonly controlUrl: string | null = null;
  private readonly auditEntries: SovereignXClusterControlAuditEntry[] = [];

  async applyControl(
    request: SovereignXClusterControlRequest,
    observedAtMs: number,
  ): Promise<SovereignXClusterControlAdapterResult> {
    const before = getSovereignXClusterControlState();
    const controlState = applySovereignXClusterControlRequest(request, observedAtMs);
    const membershipChanged =
      before.desiredNodeCount !== controlState.desiredNodeCount ||
      before.preferredFailoverNodeId !== controlState.preferredFailoverNodeId ||
      JSON.stringify(before.quarantinedNodeIds) !== JSON.stringify(controlState.quarantinedNodeIds);
    const outcome: SovereignXClusterControlOutcome = membershipChanged ? 'applied' : 'noop';
    const auditEntry: SovereignXClusterControlAuditEntry = {
      auditId: toAuditId(observedAtMs),
      requestedAtMs: observedAtMs,
      action: request.action ?? 'steady_state',
      nodeId: request.nodeId?.trim() || null,
      reason: defaultReason(request),
      outcome,
      backend: 'local',
      detail: outcome === 'noop' ? 'no membership change produced' : 'membership control applied in-process',
    };
    this.auditEntries.push(auditEntry);
    return { outcome, controlState, auditEntry };
  }

  auditTrail(): SovereignXClusterControlAuditEntry[] {
    return this.auditEntries.map((entry) => ({ ...entry }));
  }

  status(): { backend: 'local'; controlUrl: null; auditEntryCount: number } {
    return {
      backend: 'local',
      controlUrl: null,
      auditEntryCount: this.auditEntries.length,
    };
  }
}

class SovereignXRemoteClusterControlAdapter implements SovereignXClusterControlAdapter {
  readonly backend = 'remote' as const;
  readonly controlUrl: string;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;
  private readonly auditEntries: SovereignXClusterControlAuditEntry[] = [];

  constructor(options: Required<Pick<SovereignXClusterControlAdapterOptions, 'controlUrl'>> & SovereignXClusterControlAdapterOptions) {
    this.controlUrl = options.controlUrl.replace(/\/+$/, '');
    this.fetchImpl = options.fetchImpl ?? ((input, init) => fetch(input, init));
    this.timeoutMs = options.timeoutMs ?? 5_000;
  }

  async applyControl(
    request: SovereignXClusterControlRequest,
    observedAtMs: number,
  ): Promise<SovereignXClusterControlAdapterResult> {
    const auditEntryBase = {
      auditId: toAuditId(observedAtMs),
      requestedAtMs: observedAtMs,
      action: request.action ?? 'steady_state',
      nodeId: request.nodeId?.trim() || null,
      reason: defaultReason(request),
    };

    try {
      const response = await this.fetchImpl(`${this.controlUrl}/control`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ request, observedAtMs }),
        signal: AbortSignal.timeout(this.timeoutMs),
      });

      if (!response.ok) {
        const auditEntry: SovereignXClusterControlAuditEntry = {
          ...auditEntryBase,
          outcome: 'rejected',
          backend: 'remote',
          detail: `control plane rejected with HTTP ${response.status}`,
        };
        this.auditEntries.push(auditEntry);
        return { outcome: 'rejected', controlState: getSovereignXClusterControlState(), auditEntry };
      }

      const payload = (await response.json()) as { controlState?: unknown };
      if (!isControlState(payload.controlState)) {
        const auditEntry: SovereignXClusterControlAuditEntry = {
          ...auditEntryBase,
          outcome: 'rejected',
          backend: 'remote',
          detail: 'control plane returned an invalid control state payload',
        };
        this.auditEntries.push(auditEntry);
        return { outcome: 'rejected', controlState: getSovereignXClusterControlState(), auditEntry };
      }

      const controlState = replaceSovereignXClusterControlState(payload.controlState);
      const auditEntry: SovereignXClusterControlAuditEntry = {
        ...auditEntryBase,
        outcome: 'remote-applied',
        backend: 'remote',
        detail: `control plane applied membership control at ${this.controlUrl}`,
      };
      this.auditEntries.push(auditEntry);
      return { outcome: 'remote-applied', controlState, auditEntry };
    } catch (error) {
      const fallbackResult = await new SovereignXLocalClusterControlAdapter().applyControl(request, observedAtMs);
      const auditEntry: SovereignXClusterControlAuditEntry = {
        ...auditEntryBase,
        outcome: 'remote-fallback',
        backend: 'remote',
        detail: `control plane unreachable (${error instanceof Error ? error.message : String(error)}); fell back to in-process control`,
      };
      this.auditEntries.push(auditEntry);
      return {
        outcome: 'remote-fallback',
        controlState: fallbackResult.controlState,
        auditEntry,
      };
    }
  }

  auditTrail(): SovereignXClusterControlAuditEntry[] {
    return this.auditEntries.map((entry) => ({ ...entry }));
  }

  status(): { backend: 'remote'; controlUrl: string; auditEntryCount: number } {
    return {
      backend: 'remote',
      controlUrl: this.controlUrl,
      auditEntryCount: this.auditEntries.length,
    };
  }
}

export function createSovereignXClusterControlAdapter(
  options: SovereignXClusterControlAdapterOptions = {},
): SovereignXClusterControlAdapter {
  const controlUrl = options.controlUrl?.trim();
  if (controlUrl) {
    return new SovereignXRemoteClusterControlAdapter({ ...options, controlUrl });
  }
  return new SovereignXLocalClusterControlAdapter();
}

export function resetSovereignXClusterControlAdapter(): void {
  resetSovereignXClusterControlState();
}
