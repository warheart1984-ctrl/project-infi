import type { CSSProperties, ReactNode } from 'react';

import type { CoriAlphaWorkspaceSummary } from './coriAlpha.js';

export type { CoriAlphaWorkspaceSummary } from './coriAlpha.js';

export interface CoriAlphaSummaryCardProps {
  summary: CoriAlphaWorkspaceSummary | null;
  loading?: boolean;
  title?: string;
  surfaceLabel?: string;
  emptyMessage: string;
  loadingMessage?: string;
}

export function CoriAlphaSummaryCard({
  summary,
  loading = false,
  title = 'CORI Alpha upload intelligence',
  surfaceLabel = 'Shared across ops-console and the customer workspace',
  emptyMessage,
  loadingMessage = 'Loading CORI Alpha upload intelligence...',
}: CoriAlphaSummaryCardProps) {
  return (
    <section style={cardStyle}>
      <div style={eyebrowStyle}>{surfaceLabel}</div>
      <h2 style={headingStyle}>{title}</h2>
      {loading ? (
        <p style={subtleStyle}>{loadingMessage}</p>
      ) : summary ? (
        <>
          <div style={metricGridStyle}>
            <Metric label="Uploads" value={String(summary.summary.uploadCount)} />
            <Metric label="Approved" value={String(summary.summary.approvedCount)} />
            <Metric label="Blocked" value={String(summary.summary.blockedCount)} />
            <Metric label="Avg trust" value={summary.summary.averageTrustScore === null ? 'n/a' : summary.summary.averageTrustScore.toFixed(4)} />
            <Metric label="Latest commit" value={summary.summary.latestCommit ?? 'none'} />
            <Metric label="Validation" value={summary.validation.valid ? 'pass' : 'review'} />
          </div>
          <section style={subpanelGridStyle}>
            <Panel title="Repository rollup">
              <div style={{ overflowX: 'auto' }}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Repository</th>
                      <th style={thStyle}>Uploads</th>
                      <th style={thStyle}>Approved</th>
                      <th style={thStyle}>Blocked</th>
                      <th style={thStyle}>Avg trust</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(summary.summary.repositoryCounts)
                      .sort(([left], [right]) => left.localeCompare(right))
                      .map(([repository, counts]) => (
                        <tr key={repository}>
                          <td style={tdStyle}>{repository}</td>
                          <td style={tdStyle}>{counts.uploads}</td>
                          <td style={tdStyle}>{counts.approved}</td>
                          <td style={tdStyle}>{counts.blocked}</td>
                          <td style={tdStyle}>{counts.averageTrustScore === null ? 'n/a' : counts.averageTrustScore.toFixed(4)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </Panel>

            <Panel title="Recent uploads">
              {summary.uploads.length ? (
                <div style={{ overflowX: 'auto' }}>
                  <table style={tableStyle}>
                    <thead>
                      <tr>
                        <th style={thStyle}>Commit</th>
                        <th style={thStyle}>Decision</th>
                        <th style={thStyle}>Trust</th>
                        <th style={thStyle}>Mode</th>
                        <th style={thStyle}>Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.uploads.slice(-5).reverse().map((upload) => (
                        <tr key={upload.commit}>
                          <td style={tdStyle}>{upload.commit.slice(0, 12)}</td>
                          <td style={tdStyle}>{upload.decision.result}</td>
                          <td style={tdStyle}>{upload.trust.band} ({upload.trust.score.toFixed(4)})</td>
                          <td style={tdStyle}>{upload.mode}{upload.tag ? ` · ${upload.tag}` : ''}</td>
                          <td style={tdStyle}>{upload.createdAt}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p style={subtleStyle}>No CORI Alpha uploads have been recorded yet.</p>
              )}
            </Panel>

            <Panel title="Validation report">
              <div style={metricGridStyle}>
                <Metric label="Valid" value={summary.validation.valid ? 'yes' : 'no'} />
                <Metric label="Checked at" value={summary.validation.checkedAt} />
                <Metric label="Issues" value={String(summary.validation.issues.length)} />
                <Metric label="Hash mismatches" value={String(summary.validation.hashMismatches.length)} />
              </div>
              {summary.validation.issues.length ? (
                <ul style={listStyle}>
                  {summary.validation.issues.map((issue) => (
                    <li key={issue}>{issue}</li>
                  ))}
                </ul>
              ) : (
                <p style={subtleStyle}>The current CORI Alpha store validates cleanly.</p>
              )}
            </Panel>
          </section>
          <p style={subtleStyle}>
            This is the same upload intelligence surface used by the operator console and the customer workspace, backed by the shared CORI Alpha ledger in `.runtime/cori-alpha`.
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

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={panelStyle}>
      <h3 style={panelHeadingStyle}>{title}</h3>
      {children}
    </div>
  );
}

const cardStyle: CSSProperties = {
  borderRadius: 24,
  padding: 24,
  background: 'rgba(255,255,255,0.92)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  boxShadow: '0 18px 42px rgba(15, 23, 42, 0.05)',
};

const eyebrowStyle: CSSProperties = {
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

const headingStyle: CSSProperties = {
  marginTop: 12,
  marginBottom: 12,
  fontSize: '1.35rem',
};

const subtleStyle: CSSProperties = {
  color: '#475569',
  lineHeight: 1.7,
};

const metricGridStyle: CSSProperties = {
  display: 'grid',
  gap: 10,
  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
};

const metricStyle: CSSProperties = {
  padding: 12,
  borderRadius: 16,
  background: '#f8fafc',
  border: '1px solid #e2e8f0',
};

const metricLabelStyle: CSSProperties = {
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  color: '#64748b',
  marginBottom: 6,
};

const metricValueStyle: CSSProperties = {
  fontWeight: 700,
  color: '#0f172a',
  wordBreak: 'break-word',
};

const tableStyle: CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
};

const thStyle: CSSProperties = {
  textAlign: 'left',
  padding: '10px 8px',
  borderBottom: '1px solid #e2e8f0',
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  color: '#64748b',
};

const tdStyle: CSSProperties = {
  padding: '10px 8px',
  borderBottom: '1px solid #e2e8f0',
  verticalAlign: 'top',
};

const panelStyle: CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 14,
  padding: 14,
  background: '#fff',
};

const panelHeadingStyle: CSSProperties = {
  marginTop: 0,
  marginBottom: 10,
};

const subpanelGridStyle: CSSProperties = {
  display: 'grid',
  gap: 12,
  marginTop: 16,
};

const listStyle: CSSProperties = {
  margin: '12px 0 0',
  paddingLeft: 18,
  color: '#475569',
  lineHeight: 1.7,
};
