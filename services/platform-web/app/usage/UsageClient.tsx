'use client';

import { useEffect, useMemo, useState } from 'react';

import { OrgLedgerSummary, type OrgAuditSummary, type OrgUsageSummary } from '../components/OrgLedgerSummary';
import { QuotaSummary } from '../components/QuotaSummary';

type Customer = {
  id: string;
  email: string;
  planName: string;
  planId: string;
  organizationId?: string;
  organizationRole?: string;
  entitlements: {
    routingTier: string;
    codexPacketHandoff: boolean;
    usageLedger: boolean;
    marginDashboard: boolean;
    treasuryAccess: boolean;
    governanceLevel: string;
    auditScope: string;
    overageBillingEnabled: boolean;
    customerAuditSurfaces: boolean;
  };
};

type QuotaResponse = {
  customer?: Customer;
  quota: {
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
  usageRecords: { operation: string; units: number; timestamp: string; metadata?: Record<string, unknown> }[];
};

export function UsageClient() {
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [quota, setQuota] = useState<QuotaResponse | null>(null);
  const [organizationUsage, setOrganizationUsage] = useState<OrgUsageSummary | null>(null);
  const [organizationAudit, setOrganizationAudit] = useState<OrgAuditSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const organizationId = useMemo(() => customer?.organizationId ?? null, [customer]);

  function Metric({ label, value }: { label: string; value: string }) {
    return (
      <div style={metricStyle}>
        <div style={metricLabelStyle}>{label}</div>
        <div style={metricValueStyle}>{value}</div>
      </div>
    );
  }

  useEffect(() => {
    void load();
  }, []);

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const [customerRes, quotaRes] = await Promise.all([
        fetch('/api/customer/me'),
        fetch('/api/customers/quota'),
      ]);
      let customerBody: { customer?: Customer } | null = null;
      if (customerRes.ok) {
        customerBody = (await customerRes.json()) as { customer?: Customer };
        setCustomer(customerBody.customer ?? null);
      }
      let quotaBody: QuotaResponse | null = null;
      if (quotaRes.ok) {
        quotaBody = (await quotaRes.json()) as QuotaResponse;
        setQuota(quotaBody);
      }

      const activeOrgId = customerBody?.customer?.organizationId ?? quotaBody?.customer?.organizationId ?? null;
      if (activeOrgId) {
        const [usageRes, pricingRes, routingRes, entitlementsRes] = await Promise.all([
          fetch(`/api/organizations/${encodeURIComponent(activeOrgId)}/usage`),
          fetch(`/api/organizations/${encodeURIComponent(activeOrgId)}/audit/pricing`),
          fetch(`/api/organizations/${encodeURIComponent(activeOrgId)}/audit/routing`),
          fetch(`/api/organizations/${encodeURIComponent(activeOrgId)}/audit/entitlements`),
        ]);
        if (usageRes.ok) {
          setOrganizationUsage((await usageRes.json()) as OrgUsageSummary);
        } else {
          setOrganizationUsage(null);
        }
        const audit: OrgAuditSummary = {
          pricing: pricingRes.ok ? (((await pricingRes.json()) as { audit?: unknown[] }).audit ?? []) : [],
          routing: routingRes.ok ? (((await routingRes.json()) as { audit?: unknown[] }).audit ?? []) : [],
          entitlements: entitlementsRes.ok ? (((await entitlementsRes.json()) as { audit?: unknown[] }).audit ?? []) : [],
        };
        setOrganizationAudit(audit);
      } else {
        setOrganizationUsage(null);
        setOrganizationAudit(null);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={layoutStyle}>
      <section style={heroStyle}>
        <div style={eyebrowStyle}>Usage and quota</div>
        <h1 style={titleStyle}>Customer-facing usage, overage, and org audit surface</h1>
        <p style={ledeStyle}>
          This page uses the org-scoped endpoints to show request limits, token limits, overage events, and the audit packets that justify routing and pricing.
        </p>
        <div style={heroMetricsStyle}>
          <Metric label="Customer" value={customer?.email ?? 'loading'} />
          <Metric label="Organization" value={organizationId ?? 'none'} />
          <Metric label="Status" value={loading ? 'loading' : 'ready'} />
          <Metric label="Overage" value={formatCurrency(quota?.quota.overageBillingUsd ?? 0)} />
        </div>
      </section>

      {error ? <p style={errorStyle}>{error}</p> : null}

      <div style={gridStyle}>
        <QuotaSummary
          title="Quota"
          quota={quota?.quota ?? null}
          usageRecordCount={quota?.usageRecords.length ?? 0}
          emptyMessage="Quota data appears after login."
        />

      <OrgLedgerSummary
        organizationId={organizationId}
        loading={loading}
        usage={organizationUsage}
        audit={organizationAudit}
        emptyMessage="No organization usage is available until the customer belongs to an org."
      />
      </div>
    </div>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(value);
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

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 16,
  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
};

const metricStyle: React.CSSProperties = {
  padding: 12,
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

const errorStyle: React.CSSProperties = {
  color: '#b91c1c',
  fontWeight: 700,
};
