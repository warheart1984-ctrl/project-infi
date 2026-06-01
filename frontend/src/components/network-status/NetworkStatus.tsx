import React, { useMemo, useState } from 'react';
import './NetworkStatus.css';
import { NetworkStatusData, SystemMode } from './networkStatusTypes';
import {
  deriveSystemMode,
  getModeColor,
  getPulseDuration,
} from './networkStatusLogic';

interface NetworkStatusProps {
  data: NetworkStatusData | null;
  showPill?: boolean;
  providerLabels?: Record<string, string>;
}

export const NetworkStatus: React.FC<NetworkStatusProps> = ({
  data,
  showPill = true,
  providerLabels = {},
}) => {
  const [hover, setHover] = useState(false);

  const mode: SystemMode = useMemo(() => {
    if (!data) return 'critical';
    return data.system_mode || deriveSystemMode(data);
  }, [data]);

  const color = getModeColor(mode);
  const duration = getPulseDuration(mode);
  const isCritical = mode === 'critical';

  const latency = data?.latency_ms ?? null;
  const packetLoss = data?.packet_loss ?? null;
  const providers = data?.providers ?? {};
  const routing = data?.routing ?? 'failed';

  const providerEntries = Object.entries(providers);

  const ariaLabel = data
    ? `Network status: ${mode}. Latency ${latency} milliseconds. ${providerEntries.length} providers.`
    : 'Network status: unknown. Telemetry error.';

  return (
    <div className="ns-root" aria-label={ariaLabel}>
      <div
        className={[
          'ns-pulse-bar',
          isCritical ? 'ns-pulse-bar--blink' : 'ns-pulse-bar--animated',
        ].join(' ')}
        style={{
          backgroundColor: color,
          animationDuration: isCritical ? '0.5s' : duration,
        }}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
      />

      {showPill && data && (
        <div
          className="ns-pill"
          style={{ marginTop: 8, position: 'relative' }}
          onMouseEnter={() => setHover(true)}
          onMouseLeave={() => setHover(false)}
        >
          <div
            className="ns-pill-dot"
            style={{ backgroundColor: getConnectivityColor(latency) }}
          />
          <div
            className="ns-pill-dot"
            style={{ backgroundColor: getProvidersColor(providers) }}
          />
          <div
            className="ns-pill-dot"
            style={{ backgroundColor: color }}
          />
        </div>
      )}

      {hover && (
        <div className="ns-tooltip">
          <div className="ns-tooltip-section"><strong>Network Status:</strong> {mode}</div>
          {latency !== null && (
            <div className="ns-tooltip-section"><strong>Latency:</strong> {latency} ms</div>
          )}
          {packetLoss !== null && (
            <div className="ns-tooltip-section"><strong>Packet Loss:</strong> {(packetLoss * 100).toFixed(2)}%</div>
          )}
          <div className="ns-tooltip-section"><strong>Routing:</strong> {routing}</div>
          {providerEntries.length > 0 && (
            <div className="ns-tooltip-section">
              <strong>Providers:</strong>
              {providerEntries.map(([name, status]) => (
                <div key={name}>
                  {providerLabels[name] || name}: {status}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

function getConnectivityColor(latency: number | null): string {
  if (latency == null) return '#7F8C8D';
  if (latency < 80) return '#3EE68A';
  if (latency < 150) return '#F4D03F';
  if (latency < 300) return '#F39C12';
  return '#E74C3C';
}

function getProvidersColor(
  providers: Record<string, 'online' | 'degraded' | 'offline'>,
): string {
  const values = Object.values(providers);
  if (values.length === 0) return '#7F8C8D';

  const online = values.filter((value) => value === 'online').length;
  if (online === values.length) return '#3EE68A';
  if (online >= values.length / 2) return '#F4D03F';
  if (online > 0) return '#F39C12';
  return '#E74C3C';
}
