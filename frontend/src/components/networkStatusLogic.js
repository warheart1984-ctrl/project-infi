export function buildNetworkStatusData({
  latency_ms = null,
  backend_healthy = false,
  fallback_active = false,
  quarantined = false,
  timestamp = Date.now(),
  providers = [],
} = {}) {
  return {
    latency_ms,
    backend_healthy: Boolean(backend_healthy),
    fallback_active: Boolean(fallback_active),
    quarantined: Boolean(quarantined),
    timestamp,
    providers: providers.map((provider) => ({
      id: String(provider.id || 'unknown'),
      available: Boolean(provider.available),
      kind: provider.kind || 'provider',
      requested: Boolean(provider.requested),
      active: Boolean(provider.active),
      fallback_target: Boolean(provider.fallback_target),
    })),
  };
}
