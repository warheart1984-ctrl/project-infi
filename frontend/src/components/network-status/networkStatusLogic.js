export function buildNetworkStatusData({
  latency_ms = null,
  backend_healthy = false,
  fallback_active = false,
  quarantined = false,
  timestamp = Date.now(),
  providers = [],
} = {}) {
  const availableCount = providers.filter((provider) => provider.available).length;
  return {
    latency_ms,
    backend_healthy,
    fallback_active,
    quarantined,
    timestamp,
    providers,
    summary: backend_healthy ? 'healthy' : 'degraded',
    available_count: availableCount,
    total_count: providers.length,
  };
}
