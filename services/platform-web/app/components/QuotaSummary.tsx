'use client';

type QuotaData = {
  requestLimit: number;
  requestCount: number;
  requestOverage: number;
  tokenLimit: number;
  tokenCount: number;
  tokenOverage: number;
  overageBillingUsd: number;
  overageBillingEnabled: boolean;
  enforcement: {
    status: 'within_limit' | 'metered_overage' | 'blocked';
    allowed: boolean;
    reason: string;
  };
};

export interface QuotaSummaryProps {
  quota: QuotaData | null;
  usageRecordCount: number;
  title?: string;
  emptyMessage: string;
}

export function QuotaSummary({
  quota,
  usageRecordCount,
  title = 'Quota and overage',
  emptyMessage,
}: QuotaSummaryProps) {
  return (
    <section style={cardStyle}>
      <h2 style={headingStyle}>{title}</h2>
      {quota ? (
        <>
          <div style={metricGridStyle}>
            <Metric label="Requests" value={`${quota.requestCount}/${quota.requestLimit}`} />
            <Metric label="Tokens" value={`${quota.tokenCount}/${quota.tokenLimit}`} />
            <Metric label="Overage USD" value={formatCurrency(quota.overageBillingUsd)} />
            <Metric label="Status" value={quota.enforcement.status} />
          </div>
          <p style={subtleStyle}>{quota.enforcement.reason}</p>
          <p style={subtleStyle}>Usage ledger records: {usageRecordCount}</p>
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

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(value);
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
