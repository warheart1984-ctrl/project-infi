'use client';

import { useEffect, useMemo, useState } from 'react';

import type {
  ManagedServiceStatus,
  ManagedServiceSummary,
} from '../../lib/operatorConsole';

type RegistryResponse = {
  defaultServiceId: string;
  services: ManagedServiceSummary[];
};

type StatusResponse = ManagedServiceStatus & {
  result?: {
    action: string;
    ok: boolean;
    exitCode: number | null;
    stdout: string;
    stderr: string;
    error?: string;
    artifacts?: Array<{ kind: string; label: string; path: string }>;
  };
  snapshot?: ManagedServiceStatus;
  error?: string;
};

export function DropboxAutomationConsole() {
  const [services, setServices] = useState<ManagedServiceSummary[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState<string>('dropbox');
  const [status, setStatus] = useState<ManagedServiceStatus | null>(null);
  const [actionResult, setActionResult] = useState<StatusResponse['result'] | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string | null>(null);

  const selectedService = useMemo(() => {
    return services.find((service) => service.id === selectedServiceId) ?? services[0] ?? null;
  }, [selectedServiceId, services]);

  const statusSummary = useMemo(() => {
    if (!status) {
      return 'Loading operator state...';
    }

    const folder = status.syncFolderRoot ?? 'none';
    const token = status.tokenPresent ? 'present' : 'missing';
    const scope = status.selectedAccountScope ?? 'auto';
    return `health=${status.health} | backend=${status.backend} | folder=${folder} | scope=${scope} | token=${token}`;
  }, [status]);

  async function refreshRegistry(): Promise<void> {
    const response = await fetch('/api/automation', { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`registry refresh failed: ${response.status}`);
    }

    const payload = (await response.json()) as RegistryResponse;
    setServices(payload.services);
    setSelectedServiceId((current) => {
      if (payload.services.some((service) => service.id === current)) {
        return current;
      }
      return payload.defaultServiceId ?? payload.services[0]?.id ?? current;
    });
  }

  async function refreshStatus(serviceId = selectedServiceId): Promise<void> {
    const response = await fetch(`/api/automation/${serviceId}`, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`status refresh failed: ${response.status}`);
    }

    const payload = (await response.json()) as ManagedServiceStatus;
    setStatus(payload);
    setLastRefreshedAt(new Date().toLocaleTimeString());
  }

  async function runAction(action: string): Promise<void> {
    setBusyAction(action);
    setError(null);
    setActionResult(null);
    try {
      const response = await fetch(`/api/automation/${selectedServiceId}`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      const payload = (await response.json()) as StatusResponse;
      if (!response.ok) {
        throw new Error(payload.result?.error ?? payload.result?.stderr ?? payload.error ?? `action failed: ${response.status}`);
      }
      setStatus(payload.snapshot ?? payload);
      setActionResult(payload.result ?? null);
      setLastRefreshedAt(new Date().toLocaleTimeString());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusyAction(null);
    }
  }

  useEffect(() => {
    void refreshRegistry()
      .then(() => refreshStatus())
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : String(caught));
      });
  }, []);

  useEffect(() => {
    if (!selectedServiceId) {
      return;
    }

    void refreshStatus(selectedServiceId).catch((caught: unknown) => {
      setError(caught instanceof Error ? caught.message : String(caught));
    });

    const interval = window.setInterval(() => {
      void refreshStatus(selectedServiceId).catch(() => {});
    }, 5000);

    return () => window.clearInterval(interval);
  }, [selectedServiceId]);

  return (
    <section style={shellStyle}>
      <div style={statusBandStyle}>
        <div>
          <div style={kickerStyle}>Automation state</div>
          <h2 style={headlineStyle}>Constitutional Operations Console</h2>
          <p style={ledeStyle}>{statusSummary}</p>
        </div>
        <button type="button" onClick={() => void refreshStatus()} style={secondaryButtonStyle}>
          Refresh status
        </button>
      </div>

      <div style={registryGridStyle}>
        {services.map((service) => (
          <button
            key={service.id}
            type="button"
            onClick={() => setSelectedServiceId(service.id)}
            style={serviceCardStyle(service.id === selectedServiceId)}
          >
            <div style={serviceCardHeaderStyle}>
              <strong style={serviceCardTitleStyle}>{service.label}</strong>
              <span style={serviceCardBadgeStyle}>{service.id}</span>
            </div>
            <div style={serviceCardDescriptionStyle}>{service.description}</div>
            <div style={serviceCardActionsStyle}>
              {service.actions.map((action) => (
                <span key={action.action} style={serviceActionPillStyle}>
                  {action.label}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>

      <div style={gridStyle}>
        <Panel title="Service" value={status?.installed ? `${status?.serviceDisplayName} | ${status?.state}` : 'Not installed'} subvalue={`${status?.serviceVersion ?? 'v1.0.0'} | ${status?.serviceName ?? selectedService?.id ?? 'unknown'}`} />
        <Panel title="Health" value={status?.health ?? 'loading'} subvalue={status?.healthReason ?? 'Waiting for health snapshot'} />
        <Panel title="Backend" value={status?.backend ?? 'loading'} subvalue={status?.lastStartupLine ?? 'Waiting for service log'} />
        <Panel title="Conformance" value={status?.conformance?.conformanceStatus ?? 'unknown'} subvalue={`build=${status?.conformance?.buildStatus ?? 'unknown'} | runtime=${status?.conformance?.runtimeStatus ?? 'unknown'} | replay=${status?.conformance?.replayReadiness ?? 'unknown'}`} />
        <Panel title="Sync" value={status?.syncFolderRoot ?? 'none'} subvalue={`${status?.selectedAccountScope ?? 'auto'} | ${status?.tokenPresent ? 'Token present' : 'Token missing'}`} />
        <Panel title="Activity" value={status?.lastSuccessfulOperation ?? 'none yet'} subvalue={`${status?.recentTimelineEntries?.length ?? 0} timeline events`} />
      </div>

      <div style={actionsWrapStyle}>
        <div style={sectionTitleStyle}>Automation actions</div>
        <div style={actionsGridStyle}>
          {(selectedService?.actions ?? []).map((entry) => (
            <button
              key={entry.action}
              type="button"
              style={actionButtonStyle}
              onClick={() => void runAction(entry.action)}
              disabled={busyAction !== null}
            >
              <strong style={actionButtonTitleStyle}>{busyAction === entry.action ? 'Working...' : entry.label}</strong>
              <span style={actionButtonDescriptionStyle}>{entry.description}</span>
            </button>
          ))}
        </div>
      </div>

      <div style={dashboardGridStyle}>
        <article style={timelinePanelStyle}>
          <div style={sectionTitleStyle}>Operator timeline</div>
          <div style={timelineListStyle}>
            {(status?.recentTimelineEntries ?? []).length > 0 ? (
              status!.recentTimelineEntries.slice().reverse().map((entry, index) => (
                <div key={`${entry.at}-${index}`} style={timelineItemStyle}>
                  <div style={timelineTopRowStyle}>
                    <strong style={timelineTitleStyle}>{entry.title}</strong>
                    <span style={timelineMetaStyle}>{entry.kind} | {entry.severity}</span>
                  </div>
                  <div style={timelineDetailStyle}>{entry.detail}</div>
                  <div style={timelineMetaStyle}>{entry.at}</div>
                </div>
              ))
            ) : (
              <div style={timelineEmptyStyle}>No timeline entries yet. Trigger an action to populate the operator record.</div>
            )}
          </div>
        </article>

        <article style={artifactsPanelStyle}>
          <div style={sectionTitleStyle}>Constitutional artifacts</div>
          <div style={artifactListStyle}>
            {(status?.recentArtifacts ?? []).length > 0 ? (
              status!.recentArtifacts.map((artifact) => (
                <div key={artifact.path} style={artifactItemStyle}>
                  <div style={artifactTitleStyle}>{artifact.label}</div>
                  <div style={artifactMetaStyle}>{artifact.kind}</div>
                  <div style={artifactPathStyle}>{artifact.path}</div>
                </div>
              ))
            ) : (
              <div style={timelineEmptyStyle}>Artifacts will appear here after actions generate receipts, evidence, audit records, and replay metadata.</div>
            )}
          </div>
        </article>
      </div>

      <div style={logGridStyle}>
        <article style={logPanelStyle}>
          <div style={sectionTitleStyle}>Startup line</div>
          <pre style={logPreStyle}>{status?.lastStartupLine ?? 'No startup line yet.'}</pre>
        </article>
        <article style={logPanelStyle}>
          <div style={sectionTitleStyle}>Recent log</div>
          <pre style={logPreStyle}>{(status?.recentLogLines ?? ['Waiting for live log...']).join('\n')}</pre>
        </article>
      </div>

      {actionResult ? (
        <article style={resultPanelStyle}>
          <div style={sectionTitleStyle}>Last action result</div>
          <pre style={logPreStyle}>{JSON.stringify(actionResult, null, 2)}</pre>
        </article>
      ) : null}

      {error ? (
        <article style={errorPanelStyle}>
          <div style={sectionTitleStyle}>Error</div>
          <p style={{ margin: 0 }}>{error}</p>
        </article>
      ) : null}

      <div style={footerStyle}>
        <span>Last refreshed: {lastRefreshedAt ?? 'just opened'}</span>
      </div>
    </section>
  );
}

function Panel(props: { title: string; value: string; subvalue: string }) {
  return (
    <article style={panelStyle}>
      <div style={panelTitleStyle}>{props.title}</div>
      <div style={panelValueStyle}>{props.value}</div>
      <div style={panelSubvalueStyle}>{props.subvalue}</div>
    </article>
  );
}

const shellStyle: React.CSSProperties = {
  display: 'grid',
  gap: 24,
};

const statusBandStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'flex-end',
  justifyContent: 'space-between',
  gap: 16,
  flexWrap: 'wrap',
};

const kickerStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 8,
  padding: '8px 12px',
  borderRadius: 999,
  background: 'rgba(2, 132, 199, 0.12)',
  color: '#075985',
  fontSize: 12,
  fontWeight: 800,
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
};

const headlineStyle: React.CSSProperties = {
  margin: '14px 0 8px',
  fontSize: 'clamp(2rem, 4vw, 4rem)',
  letterSpacing: '-0.06em',
  lineHeight: 0.95,
};

const ledeStyle: React.CSSProperties = {
  margin: 0,
  maxWidth: 760,
  color: '#475569',
  lineHeight: 1.7,
};

const secondaryButtonStyle: React.CSSProperties = {
  border: '1px solid rgba(15, 23, 42, 0.15)',
  background: '#fff',
  color: '#0f172a',
  padding: '12px 16px',
  borderRadius: 999,
  fontWeight: 700,
  cursor: 'pointer',
};

const registryGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
  gap: 14,
};

const serviceCardStyle = (selected: boolean): React.CSSProperties => ({
  textAlign: 'left',
  border: selected ? '1px solid rgba(2, 132, 199, 0.36)' : '1px solid rgba(15, 23, 42, 0.1)',
  background: selected
    ? 'linear-gradient(180deg, rgba(240,249,255,0.98), rgba(224,242,254,0.86))'
    : 'linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,250,252,0.92))',
  padding: 18,
  borderRadius: 20,
  cursor: 'pointer',
  display: 'grid',
  gap: 10,
  boxShadow: selected ? '0 16px 36px rgba(2, 132, 199, 0.12)' : '0 12px 30px rgba(15, 23, 42, 0.04)',
});

const serviceCardHeaderStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  gap: 12,
  flexWrap: 'wrap',
};

const serviceCardTitleStyle: React.CSSProperties = {
  fontSize: 18,
  color: '#0f172a',
};

const serviceCardBadgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  padding: '4px 10px',
  borderRadius: 999,
  background: 'rgba(14, 165, 233, 0.12)',
  color: '#075985',
  fontSize: 11,
  fontWeight: 800,
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
};

const serviceCardDescriptionStyle: React.CSSProperties = {
  color: '#475569',
  lineHeight: 1.6,
};

const serviceCardActionsStyle: React.CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 8,
};

const serviceActionPillStyle: React.CSSProperties = {
  display: 'inline-flex',
  padding: '6px 10px',
  borderRadius: 999,
  background: 'rgba(255,255,255,0.9)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  color: '#0f172a',
  fontSize: 12,
  fontWeight: 700,
};

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
  gap: 14,
};

const panelStyle: React.CSSProperties = {
  padding: 20,
  borderRadius: 22,
  background: 'rgba(255,255,255,0.78)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  boxShadow: '0 20px 60px rgba(15, 23, 42, 0.06)',
};

const panelTitleStyle: React.CSSProperties = {
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.1em',
  color: '#64748b',
  fontWeight: 800,
};

const panelValueStyle: React.CSSProperties = {
  marginTop: 10,
  fontSize: 22,
  fontWeight: 800,
  color: '#0f172a',
  wordBreak: 'break-word',
};

const panelSubvalueStyle: React.CSSProperties = {
  marginTop: 8,
  fontSize: 13,
  lineHeight: 1.6,
  color: '#475569',
  wordBreak: 'break-word',
};

const actionsWrapStyle: React.CSSProperties = {
  display: 'grid',
  gap: 14,
};

const sectionTitleStyle: React.CSSProperties = {
  fontSize: 13,
  textTransform: 'uppercase',
  letterSpacing: '0.1em',
  color: '#64748b',
  fontWeight: 800,
};

const actionsGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
  gap: 14,
};

const actionButtonStyle: React.CSSProperties = {
  textAlign: 'left',
  border: '1px solid rgba(15, 23, 42, 0.1)',
  background: 'linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,250,252,0.92))',
  padding: 18,
  borderRadius: 20,
  cursor: 'pointer',
  display: 'grid',
  gap: 8,
  boxShadow: '0 12px 30px rgba(15, 23, 42, 0.04)',
};

const actionButtonTitleStyle: React.CSSProperties = {
  fontSize: 16,
  color: '#0f172a',
};

const actionButtonDescriptionStyle: React.CSSProperties = {
  color: '#475569',
  lineHeight: 1.6,
};

const dashboardGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
  gap: 14,
};

const timelinePanelStyle: React.CSSProperties = {
  padding: 20,
  borderRadius: 20,
  background: 'rgba(255,255,255,0.8)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  boxShadow: '0 20px 60px rgba(15, 23, 42, 0.06)',
};

const artifactsPanelStyle: React.CSSProperties = {
  padding: 20,
  borderRadius: 20,
  background: 'rgba(15, 23, 42, 0.96)',
  color: '#dbeafe',
};

const timelineListStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  marginTop: 12,
};

const timelineItemStyle: React.CSSProperties = {
  padding: 14,
  borderRadius: 16,
  background: 'rgba(248,250,252,0.96)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  display: 'grid',
  gap: 8,
};

const timelineTopRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  gap: 12,
  flexWrap: 'wrap',
};

const timelineTitleStyle: React.CSSProperties = {
  color: '#0f172a',
};

const timelineDetailStyle: React.CSSProperties = {
  color: '#334155',
  lineHeight: 1.6,
};

const timelineMetaStyle: React.CSSProperties = {
  color: '#64748b',
  fontSize: 12,
  letterSpacing: '0.04em',
  textTransform: 'uppercase',
};

const timelineEmptyStyle: React.CSSProperties = {
  padding: 16,
  borderRadius: 16,
  background: 'rgba(241,245,249,0.72)',
  color: '#475569',
  lineHeight: 1.6,
};

const artifactListStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  marginTop: 12,
};

const artifactItemStyle: React.CSSProperties = {
  padding: 14,
  borderRadius: 16,
  background: 'rgba(15, 23, 42, 0.56)',
  border: '1px solid rgba(148, 163, 184, 0.2)',
  display: 'grid',
  gap: 6,
};

const artifactTitleStyle: React.CSSProperties = {
  color: '#f8fafc',
  fontWeight: 800,
};

const artifactMetaStyle: React.CSSProperties = {
  color: '#93c5fd',
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
};

const artifactPathStyle: React.CSSProperties = {
  color: '#dbeafe',
  fontSize: 12,
  lineHeight: 1.6,
  wordBreak: 'break-word',
};

const logGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
  gap: 14,
};

const logPanelStyle: React.CSSProperties = {
  padding: 20,
  borderRadius: 20,
  background: '#0f172a',
  color: '#dbeafe',
};

const logPreStyle: React.CSSProperties = {
  margin: '12px 0 0',
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
  lineHeight: 1.7,
  color: 'inherit',
  fontSize: 13,
};

const resultPanelStyle: React.CSSProperties = {
  padding: 20,
  borderRadius: 20,
  background: 'rgba(15, 118, 110, 0.12)',
  border: '1px solid rgba(15, 118, 110, 0.28)',
};

const errorPanelStyle: React.CSSProperties = {
  padding: 20,
  borderRadius: 20,
  background: 'rgba(220, 38, 38, 0.12)',
  border: '1px solid rgba(220, 38, 38, 0.24)',
  color: '#7f1d1d',
};

const footerStyle: React.CSSProperties = {
  paddingTop: 4,
  color: '#64748b',
  fontSize: 13,
};
