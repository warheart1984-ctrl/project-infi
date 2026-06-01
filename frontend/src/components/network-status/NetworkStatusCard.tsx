import React from 'react';
import { FiGlobe, FiRefreshCw } from 'react-icons/fi';
import { NetworkStatus } from './NetworkStatus';
import {
  formatRoutingLabel,
  formatSystemMode,
  getModeColor,
  getModeSurface,
  getProviderStatusColor,
  getProviderStatusLabel,
} from './networkStatusLogic';
import { NetworkStatusData } from './networkStatusTypes';

interface NetworkStatusCardProps {
  data: NetworkStatusData | null;
  providerLabels?: Record<string, string>;
  activeProviderLabel?: string | null;
  lastUpdatedLabel?: string | null;
  busy?: boolean;
  onRefresh?: (() => void) | null;
}

export const NetworkStatusCard: React.FC<NetworkStatusCardProps> = ({
  data,
  providerLabels = {},
  activeProviderLabel = null,
  lastUpdatedLabel = null,
  busy = false,
  onRefresh = null,
}) => {
  const mode = data?.system_mode || 'critical';
  const modeColor = getModeColor(mode);
  const providerEntries = Object.entries(data?.providers || {});

  return (
    <div className="jarvis-side-card page-panel network-status-card">
      <div className="network-status-head">
        <div className="jarvis-side-title">
          <FiGlobe />
          <h3>Network Status</h3>
        </div>
        {onRefresh ? (
          <button
            type="button"
            className="compact-action-button"
            onClick={onRefresh}
            disabled={busy}
            aria-label="Refresh network status"
          >
            <FiRefreshCw />
          </button>
        ) : null}
      </div>

      <div className="network-status-summary">
        <div>
          <span>Routing fabric</span>
          <strong>{formatSystemMode(mode)}</strong>
        </div>
        <span
          className="network-status-mode-chip"
          style={{
            color: modeColor,
            background: getModeSurface(mode),
          }}
        >
          {formatRoutingLabel(data?.routing || 'failed')}
        </span>
      </div>

      <NetworkStatus
        data={data}
        providerLabels={providerLabels}
      />

      <div className="network-status-grid">
        <div className="network-status-stat">
          <span>Latency</span>
          <strong>{data ? `${data.latency_ms} ms` : 'Unknown'}</strong>
        </div>
        <div className="network-status-stat">
          <span>Packet Loss</span>
          <strong>{data ? `${(data.packet_loss * 100).toFixed(1)}%` : 'Unknown'}</strong>
        </div>
        <div className="network-status-stat">
          <span>Fallback</span>
          <strong>{data?.fallback_active ? 'Active' : 'Clear'}</strong>
        </div>
        <div className="network-status-stat">
          <span>Providers</span>
          <strong>{providerEntries.length}</strong>
        </div>
      </div>

      {providerEntries.length > 0 ? (
        <div className="network-status-provider-list">
          {providerEntries.map(([providerId, status]) => (
            <div key={providerId} className="network-status-provider-row">
              <div className="network-status-provider-meta">
                <strong>{providerLabels[providerId] || providerId}</strong>
                <span>{providerId}</span>
              </div>
              <span
                className="network-status-provider-badge"
                style={{ color: getProviderStatusColor(status) }}
              >
                <span className="network-status-provider-dot" />
                {getProviderStatusLabel(status)}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      <div className="network-status-footer">
        <span>{lastUpdatedLabel ? `Updated ${lastUpdatedLabel}` : 'Waiting on telemetry'}</span>
        {activeProviderLabel ? <span>Active route: {activeProviderLabel}</span> : null}
      </div>
    </div>
  );
};
