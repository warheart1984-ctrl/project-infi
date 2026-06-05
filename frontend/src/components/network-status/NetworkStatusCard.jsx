import React from 'react';
import { FiRefreshCw } from 'react-icons/fi';

export function NetworkStatusCard({
  data = null,
  providerLabels = {},
  activeProviderLabel = '—',
  lastUpdatedLabel = '—',
  busy = false,
  onRefresh = () => {},
}) {
  const providers = Array.isArray(data?.providers) ? data.providers : [];

  return (
    <div className="jarvis-side-card page-panel" data-testid="network-status-card">
      <div className="jarvis-side-title">
        <FiRefreshCw />
        <h3>Network status</h3>
        <button type="button" className="workbench-button ghost" onClick={onRefresh} disabled={busy}>
          Refresh
        </button>
      </div>
      <p className="workbench-muted">
        Backend {data?.backend_healthy ? 'healthy' : 'degraded'} · active {activeProviderLabel} · {lastUpdatedLabel}
      </p>
      <div className="workbench-chip-row">
        <span className={`workbench-chip ${data?.backend_healthy ? 'aligned' : 'missing'}`}>
          latency={data?.latency_ms ?? '—'}ms
        </span>
        {data?.fallback_active ? <span className="workbench-chip warning">fallback</span> : null}
        {data?.quarantined ? <span className="workbench-chip missing">quarantined</span> : null}
      </div>
      <div className="workbench-history-list">
        {providers.slice(0, 6).map((provider) => (
          <div key={provider.id} className="workbench-history-item">
            <strong>{providerLabels[provider.id] || provider.id}</strong>
            <span className={`workbench-chip ${provider.available ? 'aligned' : 'missing'}`}>
              {provider.available ? 'available' : 'unavailable'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
