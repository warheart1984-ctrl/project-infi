'use client';

import { useEffect, useMemo, useState } from 'react';

import { CepOrchestratorClient, type CepArtifactExport, type CepArtifactKind, type CepArtifactRecord, type CepViewState } from '../../lib/cepOrchestratorClient';

type CepRemoteResponse = {
  viewState: CepViewState;
};

type CustomerMeResponse = {
  customer?: {
    organizationId?: string;
  };
  session?: {
    organizationId?: string;
  };
};

export function CepArtifactsClient() {
  const [exportData, setExportData] = useState<CepArtifactExport | null>(null);
  const [viewState, setViewState] = useState<CepViewState | null>(null);
  const [selectedKind, setSelectedKind] = useState<CepArtifactKind>('decision');
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<CepArtifactRecord | null>(null);
  const [customerOrganizationId, setCustomerOrganizationId] = useState<string | null>(null);
  const [selectedOrganizationId, setSelectedOrganizationId] = useState<string | null | undefined>(undefined);
  const [status, setStatus] = useState<string>('loading');
  const [error, setError] = useState<string | null>(null);
  const orchestrator = useMemo(() => new CepOrchestratorClient(), []);

  useEffect(() => {
    void refresh();
  }, []);

  async function refresh(scopeOrganizationId: string | null | undefined = selectedOrganizationId) {
    try {
      setStatus('loading');
      setError(null);
      const [customerRes, viewRes] = await Promise.all([
        fetch('/api/customer/me'),
        fetch('/api/cep/view-state'),
      ]);
      if (!viewRes.ok) {
        throw new Error(`failed to load CEP view state: ${viewRes.status}`);
      }
      const customerBody = customerRes.ok ? (await customerRes.json()) as CustomerMeResponse : null;
      const currentOrgId = customerBody?.customer?.organizationId ?? customerBody?.session?.organizationId ?? null;
      if (currentOrgId && !customerOrganizationId) {
        setCustomerOrganizationId(currentOrgId);
      }
      const effectiveOrganizationId =
        scopeOrganizationId === undefined
          ? currentOrgId
          : scopeOrganizationId;
      if (scopeOrganizationId === undefined && currentOrgId && selectedOrganizationId === undefined) {
        setSelectedOrganizationId(currentOrgId);
      }
      const exportBody = await orchestrator.getExport({ organizationId: effectiveOrganizationId ?? undefined });
      const viewBody = (await viewRes.json()) as CepRemoteResponse;
      setExportData(exportBody);
      setViewState(viewBody.viewState);
      setSelectedKind(viewBody.viewState.selectedKind);
      const resolvedArtifact =
        resolveSelectedArtifact(exportBody, viewBody.viewState.selectedArtifactId) ??
        exportBody.records.find((record) => record.kind === viewBody.viewState.selectedKind) ??
        exportBody.records[0] ??
        null;
      setSelectedArtifactId(resolvedArtifact?.id ?? null);
      setSelectedArtifact(resolvedArtifact);
      setStatus('loaded');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
      setStatus('error');
    }
  }

  const records = exportData?.records ?? [];
  const filteredRecords = records.filter((record) => record.kind === selectedKind);
  const activeOrganizationScope = selectedOrganizationId === undefined ? customerOrganizationId : selectedOrganizationId;

  async function selectArtifact(record: CepArtifactRecord) {
    setSelectedKind(record.kind);
    setSelectedArtifactId(record.id);
    setSelectedArtifact(record);
    try {
      const response = await orchestrator.setViewState({ selectedKind: record.kind, selectedArtifactId: record.id });
      setViewState(response.viewState);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    }
  }

  async function setScope(organizationId: string | null) {
    setSelectedOrganizationId(organizationId);
    await refresh(organizationId);
  }

  async function publishBundle() {
    try {
      setStatus('loading');
      setError(null);
      const sync = await orchestrator.syncBundle({
        promotionRequest: {
          source: 'platform-web',
          organizationId: activeOrganizationScope ?? undefined,
          scope: 'customer-facing-cep-surface',
        },
        replayJob: {
          source: 'platform-web',
          organizationId: activeOrganizationScope ?? undefined,
          window: {
            start: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
            end: new Date().toISOString(),
          },
        },
        decision: {
          source: 'platform-web',
          organizationId: activeOrganizationScope ?? undefined,
          verdict: 'APPROVED',
          reason: 'customer-facing CEP surface sync',
        },
      });
      setViewState(sync.viewState);
      await refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
      setStatus('error');
    }
  }

  return (
    <div style={layoutStyle}>
      <section style={heroStyle}>
        <div style={eyebrowStyle}>CEP artifact surface</div>
        <h1 style={titleStyle}>Customer-facing artifact export and view-state, mirrored from ops-console</h1>
        <p style={ledeStyle}>
          Promotion requests, replay jobs, and decisions are exposed here through the same artifact model the ops console uses. The orchestrator client can publish a bundle and keep the remote view state synchronized.
        </p>
        <div style={heroMetricsStyle}>
          <Metric label="Entries" value={String(exportData?.entryCount ?? 0)} />
          <Metric label="Promotion requests" value={String(exportData?.countsByKind['promotion-request'] ?? 0)} />
          <Metric label="Replay jobs" value={String(exportData?.countsByKind['replay-job'] ?? 0)} />
          <Metric label="Decisions" value={String(exportData?.countsByKind.decision ?? 0)} />
          <Metric label="Organization" value={activeOrganizationScope ?? 'all orgs'} />
        </div>
        <div style={scopeRowStyle}>
          <span style={scopeLabelStyle}>Artifact scope</span>
          <div style={scopeButtonGroupStyle}>
            <button
              type="button"
              style={{ ...scopeButtonStyle, ...(selectedOrganizationId === null ? scopeButtonActiveStyle : {}) }}
              onClick={() => void setScope(null)}
            >
              All organizations
            </button>
            {customerOrganizationId ? (
              <button
                type="button"
                style={{ ...scopeButtonStyle, ...(selectedOrganizationId === customerOrganizationId ? scopeButtonActiveStyle : {}) }}
                onClick={() => void setScope(customerOrganizationId)}
              >
                Current organization
              </button>
            ) : null}
          </div>
        </div>
        <div style={buttonRowStyle}>
          <button type="button" style={primaryButtonStyle} onClick={() => void publishBundle()}>
            Publish sample CEP bundle
          </button>
          <button type="button" style={secondaryButtonStyle} onClick={() => void refresh()}>
            Refresh surface
          </button>
        </div>
      </section>

      <section style={cardStyle}>
        <div style={sectionHeaderStyle}>
          <h2 style={headingStyle}>View state</h2>
          <span style={badgeStyle}>{status}</span>
        </div>
        {viewState ? (
          <div style={metricGridStyle}>
            <Metric label="Selected kind" value={viewState.selectedKind} />
            <Metric label="Selected artifact" value={viewState.selectedArtifactId ?? 'none'} />
            <Metric label="Source" value={viewState.source} />
            <Metric label="Updated" value={viewState.updatedAt} />
          </div>
        ) : (
          <p style={subtleStyle}>Load the remote CEP view state to see the customer-facing selection.</p>
        )}
      </section>

      <section style={cardStyle}>
        <div style={sectionHeaderStyle}>
          <h2 style={headingStyle}>Artifact viewer</h2>
          <div style={segmentedStyle}>
            {(['promotion-request', 'replay-job', 'decision'] as CepArtifactKind[]).map((kind) => (
              <button
                key={kind}
                type="button"
                style={{ ...segmentButtonStyle, ...(selectedKind === kind ? segmentButtonActiveStyle : {}) }}
                onClick={() => {
                  setSelectedKind(kind);
                  setSelectedArtifactId(null);
                  setSelectedArtifact(null);
                }}
              >
                {kind}
              </button>
            ))}
          </div>
        </div>
        <div style={gridStyle}>
          <div style={listStyle}>
            {filteredRecords.map((record) => (
              <button
                key={record.id}
                type="button"
                style={{ ...recordButtonStyle, ...(selectedArtifactId === record.id ? recordButtonActiveStyle : {}) }}
                onClick={() => void selectArtifact(record)}
              >
                <div style={recordTitleStyle}>{record.title}</div>
                <div style={recordMetaStyle}>{record.id}</div>
                <div style={recordMetaStyle}>{record.organizationId ?? 'all orgs'}</div>
                <div style={recordMetaStyle}>{record.source}</div>
                <div style={recordMetaStyle}>{record.recordedAt}</div>
              </button>
            ))}
            {filteredRecords.length === 0 ? <p style={subtleStyle}>No artifacts for this kind yet.</p> : null}
          </div>

          <div style={detailStyle}>
            {selectedArtifact ? (
              <>
                <div style={sectionHeaderStyle}>
                  <h3 style={headingStyle}>{selectedArtifact.title}</h3>
                  <span style={badgeStyle}>{selectedArtifact.kind}</span>
                </div>
                <p style={subtleStyle}>Source {selectedArtifact.source}</p>
                <p style={subtleStyle}>Organization {selectedArtifact.organizationId ?? 'all orgs'}</p>
                <p style={subtleStyle}>Related artifact {selectedArtifact.relatedArtifactId ?? 'none'}</p>
                <p style={subtleStyle}>Signature {selectedArtifact.signature ?? 'unsigned'}</p>
                <pre style={preStyle}>{JSON.stringify(selectedArtifact.payload, null, 2)}</pre>
              </>
            ) : (
              <p style={subtleStyle}>Select an artifact to inspect its payload and lineage.</p>
            )}
          </div>
        </div>
      </section>

      <section style={cardStyle}>
        <h2 style={headingStyle}>Export bundle</h2>
        <p style={subtleStyle}>Store {exportData?.storePath ?? 'loading'} | Recent records {exportData?.recentRecords.length ?? 0} | Scope {exportData?.organizationId ?? activeOrganizationScope ?? 'all orgs'}</p>
        <pre style={preStyle}>{JSON.stringify(exportData, null, 2)}</pre>
      </section>

      {error ? <p style={errorStyle}>{error}</p> : null}
    </div>
  );
}

function resolveSelectedArtifact(exportData: CepArtifactExport, artifactId: string | null): CepArtifactRecord | null {
  if (!artifactId) {
    return null;
  }
  return exportData.records.find((record) => record.id === artifactId) ?? null;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={metricStyle}>
      <div style={metricLabelStyle}>{label}</div>
      <div style={metricValueStyle}>{value}</div>
    </div>
  );
}

const layoutStyle: React.CSSProperties = {
  display: 'grid',
  gap: 20,
};

const heroStyle: React.CSSProperties = {
  borderRadius: 28,
  padding: 28,
  background: 'linear-gradient(145deg, rgba(15, 118, 110, 0.12), rgba(2, 132, 199, 0.08)), rgba(255,255,255,0.92)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  boxShadow: '0 30px 60px rgba(15, 23, 42, 0.08)',
};

const eyebrowStyle: React.CSSProperties = {
  display: 'inline-flex',
  padding: '8px 12px',
  borderRadius: 999,
  fontSize: 12,
  fontWeight: 800,
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
  color: '#115e59',
  background: 'rgba(15, 118, 110, 0.12)',
};

const titleStyle: React.CSSProperties = {
  margin: '16px 0 0',
  fontSize: 'clamp(2rem, 4vw, 3.8rem)',
  lineHeight: 1,
  letterSpacing: '-0.05em',
};

const ledeStyle: React.CSSProperties = {
  maxWidth: 920,
  margin: '14px 0 0',
  color: '#475569',
  lineHeight: 1.7,
};

const heroMetricsStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
  marginTop: 20,
};

const buttonRowStyle: React.CSSProperties = {
  display: 'flex',
  gap: 10,
  flexWrap: 'wrap',
  marginTop: 20,
};

const primaryButtonStyle: React.CSSProperties = {
  border: 'none',
  borderRadius: 999,
  padding: '12px 16px',
  background: 'linear-gradient(135deg, #0f766e, #0284c7)',
  color: '#fff',
  fontWeight: 700,
  cursor: 'pointer',
};

const secondaryButtonStyle: React.CSSProperties = {
  ...primaryButtonStyle,
  background: '#fff',
  color: '#0f172a',
  border: '1px solid #cbd5e1',
};

const cardStyle: React.CSSProperties = {
  borderRadius: 24,
  padding: 24,
  background: 'rgba(255,255,255,0.92)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  boxShadow: '0 18px 42px rgba(15, 23, 42, 0.05)',
};

const headingStyle: React.CSSProperties = {
  marginTop: 0,
  marginBottom: 12,
  fontSize: '1.35rem',
};

const subtleStyle: React.CSSProperties = {
  color: '#475569',
  lineHeight: 1.7,
};

const sectionHeaderStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  gap: 12,
  alignItems: 'center',
  flexWrap: 'wrap',
};

const badgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '6px 10px',
  borderRadius: 999,
  background: '#eef2ff',
  color: '#3730a3',
  fontSize: 12,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
};

const metricGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 10,
  gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
};

const metricStyle: React.CSSProperties = {
  padding: 14,
  borderRadius: 16,
  background: '#f8fafc',
  border: '1px solid #e2e8f0',
};

const metricLabelStyle: React.CSSProperties = {
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  color: '#64748b',
  marginBottom: 6,
};

const metricValueStyle: React.CSSProperties = {
  fontWeight: 700,
  color: '#0f172a',
};

const segmentedStyle: React.CSSProperties = {
  display: 'flex',
  gap: 8,
  flexWrap: 'wrap',
};

const segmentButtonStyle: React.CSSProperties = {
  border: '1px solid #cbd5e1',
  borderRadius: 999,
  padding: '8px 12px',
  background: '#fff',
  color: '#0f172a',
  cursor: 'pointer',
  fontWeight: 700,
};

const segmentButtonActiveStyle: React.CSSProperties = {
  background: '#0f172a',
  color: '#fff',
  borderColor: '#0f172a',
};

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 16,
  gridTemplateColumns: 'minmax(280px, 0.9fr) minmax(320px, 1.1fr)',
};

const listStyle: React.CSSProperties = {
  display: 'grid',
  gap: 10,
};

const recordButtonStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 14,
  background: '#fff',
  padding: 14,
  textAlign: 'left',
  cursor: 'pointer',
  display: 'grid',
  gap: 4,
};

const recordButtonActiveStyle: React.CSSProperties = {
  borderColor: '#0f766e',
  boxShadow: '0 0 0 2px rgba(15, 118, 110, 0.12)',
};

const recordTitleStyle: React.CSSProperties = {
  fontWeight: 800,
  color: '#0f172a',
};

const recordMetaStyle: React.CSSProperties = {
  fontSize: 12,
  color: '#64748b',
  wordBreak: 'break-word',
};

const scopeRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  gap: 12,
  alignItems: 'center',
  flexWrap: 'wrap',
  marginTop: 16,
};

const scopeLabelStyle: React.CSSProperties = {
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  color: '#64748b',
  fontWeight: 700,
};

const scopeButtonGroupStyle: React.CSSProperties = {
  display: 'flex',
  gap: 8,
  flexWrap: 'wrap',
};

const scopeButtonStyle: React.CSSProperties = {
  border: '1px solid #cbd5e1',
  borderRadius: 999,
  padding: '8px 12px',
  background: '#fff',
  color: '#0f172a',
  cursor: 'pointer',
  fontWeight: 700,
};

const scopeButtonActiveStyle: React.CSSProperties = {
  background: '#0f172a',
  color: '#fff',
  borderColor: '#0f172a',
};

const detailStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 16,
  padding: 16,
  background: '#fbfdff',
  minHeight: 320,
};

const preStyle: React.CSSProperties = {
  margin: 0,
  padding: 16,
  borderRadius: 14,
  background: '#0f172a',
  color: '#e2e8f0',
  overflowX: 'auto',
  lineHeight: 1.5,
  fontSize: 12,
};

const errorStyle: React.CSSProperties = {
  color: '#b91c1c',
  fontWeight: 700,
};
