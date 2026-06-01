import { tokens } from './designTokens';
import {
  BuildNetworkStatusOptions,
  NetworkStatusData,
  NetworkProviderProbe,
  ProviderStatus,
  SystemMode,
} from './networkStatusTypes';

export function deriveSystemMode(data: NetworkStatusData): SystemMode {
  const { latency_ms, providers, fallback_active } = data;

  const providerValues = Object.values(providers);
  const onlineCount = providerValues.filter((provider) => provider === 'online').length;

  if (fallback_active) return 'degraded';

  if (latency_ms >= 300 || onlineCount === 0) return 'critical';
  if (latency_ms >= 150 || onlineCount <= providerValues.length / 2) {
    return 'degraded';
  }
  if (latency_ms >= 80) return 'strained';

  return 'nominal';
}

export function getModeColor(mode: SystemMode): string {
  switch (mode) {
    case 'nominal':
      return tokens.color.status.green500;
    case 'strained':
      return tokens.color.status.yellow500;
    case 'degraded':
      return tokens.color.status.orange500;
    case 'critical':
      return tokens.color.status.red500;
    case 'quarantine':
      return tokens.color.status.purple500;
    default:
      return tokens.color.status.gray600;
  }
}

export function getModeSurface(mode: SystemMode): string {
  switch (mode) {
    case 'nominal':
      return 'rgba(62, 230, 138, 0.14)';
    case 'strained':
      return 'rgba(244, 208, 63, 0.14)';
    case 'degraded':
      return 'rgba(243, 156, 18, 0.14)';
    case 'critical':
      return 'rgba(231, 76, 60, 0.14)';
    case 'quarantine':
      return 'rgba(155, 89, 182, 0.14)';
    default:
      return 'rgba(127, 140, 141, 0.14)';
  }
}

export function getPulseDuration(mode: SystemMode): string {
  switch (mode) {
    case 'nominal':
      return '2.5s';
    case 'strained':
      return '1.8s';
    case 'degraded':
      return '1.2s';
    case 'critical':
      return '0.5s';
    case 'quarantine':
      return '3.5s';
    default:
      return '2.5s';
  }
}

export function getProviderStatusColor(status: ProviderStatus): string {
  switch (status) {
    case 'online':
      return tokens.color.status.green500;
    case 'degraded':
      return tokens.color.status.orange500;
    case 'offline':
      return tokens.color.status.red500;
    default:
      return tokens.color.status.gray600;
  }
}

export function getProviderStatusLabel(status: ProviderStatus): string {
  if (status === 'online') return 'Online';
  if (status === 'degraded') return 'Degraded';
  if (status === 'offline') return 'Offline';
  return 'Unknown';
}

export function formatSystemMode(mode: SystemMode): string {
  return `${mode || 'critical'}`
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function formatRoutingLabel(routing: NetworkStatusData['routing']): string {
  return `${routing || 'failed'}`
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function resolveProviderStatus(
  provider: NetworkProviderProbe,
  {
    backendHealthy,
    fallbackActive,
    latencyMs,
  }: {
    backendHealthy: boolean;
    fallbackActive: boolean;
    latencyMs: number;
  },
): ProviderStatus {
  if (!backendHealthy || provider.available === false) {
    return 'offline';
  }

  if (
    provider.fallback_target
    || (fallbackActive && provider.requested && !provider.active)
    || (provider.kind !== 'local' && latencyMs >= 180)
  ) {
    return 'degraded';
  }

  return 'online';
}

export function buildNetworkStatusData({
  latency_ms,
  providers = [],
  backend_healthy = true,
  fallback_active = false,
  quarantined = false,
  timestamp = Date.now(),
}: BuildNetworkStatusOptions): NetworkStatusData {
  const resolvedLatency = Math.max(
    0,
    Math.round(
      Number.isFinite(Number(latency_ms))
        ? Number(latency_ms)
        : backend_healthy
        ? 48
        : 999,
    ),
  );

  const providerStatuses = providers.reduce<Record<string, ProviderStatus>>((accumulator, provider) => {
    accumulator[provider.id] = resolveProviderStatus(provider, {
      backendHealthy: backend_healthy,
      fallbackActive: fallback_active,
      latencyMs: resolvedLatency,
    });
    return accumulator;
  }, {});

  const values = Object.values(providerStatuses);
  const totalProviders = values.length;
  const onlineCount = values.filter((value) => value === 'online').length;
  const degradedCount = values.filter((value) => value === 'degraded').length;
  const offlineCount = values.filter((value) => value === 'offline').length;

  const routing: NetworkStatusData['routing'] = !backend_healthy || onlineCount === 0
    ? 'failed'
    : fallback_active || degradedCount > 0 || offlineCount > 0
    ? 'unstable'
    : 'stable';

  const offlineRatio = totalProviders > 0 ? offlineCount / totalProviders : 0;
  const degradedRatio = totalProviders > 0 ? degradedCount / totalProviders : 0;
  const packetLoss = Math.min(
    0.95,
    Number(
      (
        offlineRatio * 0.35
        + degradedRatio * 0.12
        + (routing === 'unstable' ? 0.02 : 0)
        + (routing === 'failed' ? 0.18 : 0)
      ).toFixed(4),
    ),
  );

  const data: NetworkStatusData = {
    latency_ms: resolvedLatency,
    packet_loss: packetLoss,
    providers: providerStatuses,
    routing,
    system_mode: 'nominal',
    fallback_active: fallback_active,
    timestamp,
  };

  data.system_mode = quarantined
    ? 'quarantine'
    : deriveSystemMode(data);

  return data;
}
