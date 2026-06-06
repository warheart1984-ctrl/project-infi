import React from 'react';
import { FiActivity, FiRefreshCw, FiWifi, FiWifiOff } from 'react-icons/fi';

function toneForProvider(provider) {
  if (provider.active) {
    return 'aligned';
  }
  if (provider.fallback_target || provider.requested) {
    return 'warning';
  }
  return provider.available ? 'aligned' : 'missing';
}

export function NetworkStatusCard({
  data,
  providerLabels = {},
  activeProviderLabel = 'Local',
  lastUpdatedLabel = 'unknown',
  busy = false,
  onRefresh,
}) {
  const state = data || {};
  const providers = state.providers || [];
  const healthy = Boolean(state.backend_healthy);

  return (
    <section className="jarvis-side-card page-panel" data-testid="network-status-card">
      <div className="jarvis-side-title">
        {healthy ? <FiWifi /> : <FiWifiOff />}
        <h3>Network Status</h3>
        <button
          type="button"
          className="jarvis-icon-button"
          onClick={onRefresh}
          disabled={busy}
          title="Refresh network status"
          aria-label="Refresh network status"
        >
          <FiRefreshCw />
        </button>
      </div>
      <div className="workbench-chip-row">
        <span className={`workbench-chip ${healthy ? 'aligned' : 'missing'}`}>
          backend={healthy ? 'healthy' : 'offline'}
        </span>
        <span className={`workbench-chip ${state.fallback_active ? 'warning' : 'aligned'}`}>
          fallback={state.fallback_active ? 'on' : 'off'}
        </span>
        <span className={`workbench-chip ${state.quarantined ? 'missing' : 'aligned'}`}>
          guard={state.quarantined ? 'paused' : 'clear'}
        </span>
      </div>
      <p className="jarvis-muted">
        <FiActivity /> Active provider: {activeProviderLabel} · latency {state.latency_ms ?? 'n/a'} ms · {lastUpdatedLabel}
      </p>
      <div className="jarvis-provider-list">
        {providers.map((provider) => (
          <div key={provider.id} className="jarvis-provider-row">
            <span>{providerLabels[provider.id] || provider.id}</span>
            <span className={`workbench-chip ${toneForProvider(provider)}`}>
              {provider.active ? 'active' : provider.fallback_target ? 'fallback' : provider.available ? 'ready' : 'off'}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
