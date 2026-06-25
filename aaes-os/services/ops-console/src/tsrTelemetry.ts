import { existsSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';

export type TsrTelemetrySummary = {
  available: boolean;
  routingPath: string;
  traceStorePath: string;
  tsrOwner: string;
  controlPlaneUrl: string;
  danielRuntimeEnabled: boolean;
  connectors: {
    daniel: string;
    nexus: string;
  };
  traceEntryCount: number;
  updatedAt?: string;
  handoffReason?: string;
};

type TsrRoutingFile = {
  version?: string;
  tsr_owner?: string;
  trace_store_path?: string;
  control_plane_url?: string;
  daniel_runtime_enabled?: boolean;
  updated_at?: string;
  handoff_reason?: string;
  connectors?: Record<string, { status?: string }>;
};

export function getTsrTelemetrySummary(
  routingPath = defaultTsrRoutingPath(),
): TsrTelemetrySummary {
  if (!existsSync(routingPath)) {
    return {
      available: false,
      routingPath,
      traceStorePath: defaultTraceStorePath(),
      tsrOwner: 'unknown',
      controlPlaneUrl: defaultControlPlaneUrl(),
      danielRuntimeEnabled: false,
      connectors: { daniel: 'unknown', nexus: 'unknown' },
      traceEntryCount: 0,
    };
  }

  const routing = JSON.parse(readFileSync(routingPath, 'utf8')) as TsrRoutingFile;
  const traceStorePath = routing.trace_store_path?.trim() || defaultTraceStorePath();
  const traceEntryCount = countJsonlLines(traceStorePath);

  return {
    available: true,
    routingPath,
    traceStorePath,
    tsrOwner: String(routing.tsr_owner ?? 'nexus'),
    controlPlaneUrl: String(routing.control_plane_url ?? defaultControlPlaneUrl()),
    danielRuntimeEnabled: Boolean(routing.daniel_runtime_enabled),
    connectors: {
      daniel: String(routing.connectors?.daniel?.status ?? 'unknown'),
      nexus: String(routing.connectors?.nexus?.status ?? 'unknown'),
    },
    traceEntryCount,
    updatedAt: routing.updated_at,
    handoffReason: routing.handoff_reason,
  };
}

function defaultTsrRoutingPath(): string {
  if (process.env.TSR_ROUTING_PATH?.trim()) {
    return path.resolve(process.env.TSR_ROUTING_PATH.trim());
  }
  const root = process.env.LAWFUL_NOVA_REPO_ROOT?.trim() || process.cwd();
  return path.resolve(root, '.runtime', 'online', 'tsr-routing.json');
}

function defaultTraceStorePath(): string {
  const root = process.env.LAWFUL_NOVA_REPO_ROOT?.trim() || process.cwd();
  return path.resolve(root, '.runtime', 'online', 'aaes_traces.jsonl');
}

function defaultControlPlaneUrl(): string {
  return process.env.NEXUS_OPS_CONSOLE_URL?.trim() || 'http://127.0.0.1:4000';
}

function countJsonlLines(storePath: string): number {
  if (!existsSync(storePath)) {
    return 0;
  }
  try {
    statSync(storePath);
  } catch {
    return 0;
  }
  return readFileSync(storePath, 'utf8')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean).length;
}
