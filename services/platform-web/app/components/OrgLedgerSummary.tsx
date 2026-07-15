'use client';

export type OrgUsageSummary = {
  organizationId: string;
  total: number;
  byKind: Record<string, number>;
  summary: { total: number; byKind: Record<string, number> };
  overageEvents: { id: string; kind: string; amount: number; occurredAt: string; metadata?: Record<string, unknown> }[];
};

export type OrgAuditSummary = {
  pricing: unknown[];
  routing: unknown[];
  entitlements: unknown[];
};

export interface OrgLedgerSummaryProps {
  organizationId: string | null;
  loading?: boolean;
  usage: OrgUsageSummary | null;
  audit: OrgAuditSummary | null;
  emptyMessage: string;
  loadingMessage?: string;
}

export function OrgLedgerSummary({
  organizationId,
  loading = false,
  usage,
  audit,
  emptyMessage,
  loadingMessage = 'Loading the shared org ledger summary...',
}: OrgLedgerSummaryProps) {
  const latestRoutingDecision = extractLatestRoutingDecision(audit?.routing ?? []);
  return (
    <section style={cardStyle}>
      <h2 style={headingStyle}>Org ledger at a glance</h2>
      {loading ? (
        <p style={subtleStyle}>{loadingMessage}</p>
      ) : usage ? (
        <>
          <div style={metricGridStyle}>
            <Metric label="Organization" value={organizationId ?? usage.organizationId} />
            <Metric label="Ledger total" value={String(usage.total)} />
            <Metric label="Overage events" value={String(usage.overageEvents.length)} />
            <Metric label="Pricing audit" value={String(audit?.pricing.length ?? 0)} />
            <Metric label="Routing audit" value={String(audit?.routing.length ?? 0)} />
            <Metric label="Entitlements audit" value={String(audit?.entitlements.length ?? 0)} />
          </div>
          <div style={{ marginTop: 16, overflowX: 'auto' }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Usage kind</th>
                  <th style={thStyle}>Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(usage.byKind)
                  .sort(([left], [right]) => left.localeCompare(right))
                  .map(([kind, count]) => (
                    <tr key={kind}>
                      <td style={tdStyle}>{kind}</td>
                      <td style={tdStyle}>{count}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <section style={subpanelGridStyle}>
            <Panel title="Overage events">
              {usage.overageEvents.length ? (
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Kind</th>
                      <th style={thStyle}>Amount</th>
                      <th style={thStyle}>Occurred</th>
                      <th style={thStyle}>Metadata</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usage.overageEvents.map((event) => (
                      <tr key={event.id}>
                        <td style={tdStyle}>{event.kind}</td>
                        <td style={tdStyle}>{formatCurrency(event.amount)}</td>
                        <td style={tdStyle}>{event.occurredAt}</td>
                        <td style={tdStyle}>
                          <pre style={preStyle}>{JSON.stringify(event.metadata ?? {}, null, 2)}</pre>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p style={subtleStyle}>No overage events have been recorded for this organization yet.</p>
              )}
            </Panel>

            <Panel title="Org audit packets">
              <div style={auditGridStyle}>
                <AuditPacketPanel title="Pricing audit" value={audit?.pricing ?? []} />
                <AuditPacketPanel title="Routing audit" value={audit?.routing ?? []} />
                <AuditPacketPanel title="Entitlements audit" value={audit?.entitlements ?? []} />
              </div>
            </Panel>

            <Panel title="Latest routing decision">
              {latestRoutingDecision ? (
                <>
                  <div style={metricGridStyle}>
                    <Metric label="Decision ID" value={latestRoutingDecision.decisionId} />
                    <Metric label="Request ID" value={latestRoutingDecision.requestId} />
                    <Metric label="Status" value={latestRoutingDecision.governanceResult} />
                    <Metric label="Trust" value={`${latestRoutingDecision.trustBand} (${latestRoutingDecision.trustScore.toFixed(2)})`} />
                  </div>
                  <p style={subtleStyle}>{latestRoutingDecision.summary}</p>
                  <pre style={preStyle}>{JSON.stringify(latestRoutingDecision.payload, null, 2)}</pre>
                </>
              ) : (
                <p style={subtleStyle}>No routing decision artifact is available yet for this organization.</p>
              )}
            </Panel>
          </section>
          <p style={subtleStyle}>
            This ledger is shared with the operator console so customer and operator views read from the same org-scoped usage and audit sources.
          </p>
        </>
      ) : (
        <p style={subtleStyle}>{emptyMessage}</p>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={metricStyle}>
      <div style={metricLabelStyle}>{label}</div>
      <div style={metricValueStyle}>{value}</div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={panelStyle}>
      <h3 style={panelHeadingStyle}>{title}</h3>
      {children}
    </div>
  );
}

function AuditPacketPanel({ title, value }: { title: string; value: unknown[] }) {
  return (
    <Panel title={title}>
      <pre style={preStyle}>{JSON.stringify(value, null, 2)}</pre>
    </Panel>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(value);
}

function extractLatestRoutingDecision(routingArtifacts: unknown[]): null | {
  decisionId: string;
  requestId: string;
  trustScore: number;
  trustBand: string;
  governanceResult: string;
  summary: string;
  payload: unknown;
} {
  const latest = routingArtifacts
    .filter((artifact): artifact is Record<string, unknown> => Boolean(artifact && typeof artifact === 'object'))
    .sort((left, right) => String(right.createdAt ?? right.recordedAt ?? '').localeCompare(String(left.createdAt ?? left.recordedAt ?? '')))[0];
  if (!latest) {
    return null;
  }

  const justification = latest.justification as Record<string, unknown> | undefined;
  const routeDecisionArtifact = justification?.routeDecisionArtifact as Record<string, unknown> | undefined;
  if (!routeDecisionArtifact) {
    return null;
  }

  const trustPacket = routeDecisionArtifact.trustPacket as Record<string, unknown> | undefined;
  const governance = routeDecisionArtifact.governance as Record<string, unknown> | undefined;
  const trust = trustPacket?.trust as Record<string, unknown> | undefined;
  const trustScore = typeof trust?.score === 'number' ? trust.score : 0;
  const trustBand = typeof trust?.band === 'string' ? trust.band : 'unknown';
  const governanceResult = typeof governance?.result === 'string' ? governance.result : 'unknown';

  return {
    decisionId: String(routeDecisionArtifact.artifactId ?? latest.id ?? 'unknown'),
    requestId: String(routeDecisionArtifact.requestId ?? latest.requestId ?? 'unknown'),
    trustScore,
    trustBand,
    governanceResult,
    summary: typeof routeDecisionArtifact.provenance === 'object'
      ? `Routing decision recorded by ${String((routeDecisionArtifact.provenance as Record<string, unknown>).originSystem ?? 'unknown')} and gated by the governance kernel.`
      : 'Routing decision recorded and gated by the governance kernel.',
    payload: routeDecisionArtifact,
  };
}

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

const tableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
};

const thStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '10px 8px',
  borderBottom: '1px solid #e2e8f0',
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  color: '#64748b',
};

const tdStyle: React.CSSProperties = {
  padding: '10px 8px',
  borderBottom: '1px solid #e2e8f0',
  verticalAlign: 'top',
};

const preStyle: React.CSSProperties = {
  margin: 0,
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
  background: '#0f172a',
  color: '#e2e8f0',
  borderRadius: 14,
  padding: 14,
};

const panelStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 14,
  padding: 14,
  background: '#fff',
};

const panelHeadingStyle: React.CSSProperties = {
  marginTop: 0,
  marginBottom: 10,
};

const subpanelGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  marginTop: 16,
};

const auditGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
};
