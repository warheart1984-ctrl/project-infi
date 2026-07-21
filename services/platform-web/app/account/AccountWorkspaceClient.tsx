'use client';

import { useEffect, useMemo, useState } from 'react';

import { OrgLedgerSummary, type OrgAuditSummary, type OrgUsageSummary } from '../components/OrgLedgerSummary';
import { QuotaSummary } from '../components/QuotaSummary';
import { CoriAlphaSummaryCard, type CoriAlphaWorkspaceSummary } from '@aaes-os/platform-core/coriAlphaSummary';

type CustomerSummary = {
  id: string;
  ownerId: string;
  email: string;
  displayName?: string;
  authProvider: 'email' | 'google' | 'microsoft' | 'github' | 'apple';
  authSubject?: string;
  planId: string;
  planName: string;
  entitlements: {
    maxRequestsPerMonth: number;
    maxTokensPerMonth: number;
    allowedModels: string[];
    routingTier: string;
    codexPacketHandoff: boolean;
    usageLedger: boolean;
    marginDashboard: boolean;
    treasuryAccess: boolean;
    governanceLevel: 'basic' | 'enhanced' | 'full';
    auditScope: 'personal' | 'team' | 'org';
    overageBillingEnabled: boolean;
    customerAuditSurfaces: boolean;
  };
  organizationId?: string;
  organizationRole?: 'owner' | 'admin' | 'analyst' | 'developer' | 'auditor';
  createdAt: string;
  updatedAt: string;
};

type CustomerSession = {
  sessionId: string;
  customerId: string;
  ownerId: string;
  email: string;
  planId: string;
  planName: string;
  entitlements: CustomerSummary['entitlements'];
  governanceProfile: 'strict' | 'balanced' | 'experimental';
  organizationId?: string;
  organizationRole?: 'owner' | 'admin' | 'analyst' | 'developer' | 'auditor';
  createdAt: string;
  expiresAt: string;
};

type OrganizationRecord = {
  id: string;
  name: string;
  ownerCustomerId: string;
  planId: string;
  billingContactEmail: string;
  domain?: string;
  members: { customerId: string; role: 'owner' | 'admin' | 'analyst' | 'developer' | 'auditor'; joinedAt: string }[];
  createdAt: string;
  updatedAt: string;
};

type QuotaResponse = {
  customer: CustomerSummary;
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
  usageRecords: { operation: string; units: number; metadata?: Record<string, unknown>; timestamp: string }[];
};

const oauthProviders: Array<'google' | 'microsoft' | 'github' | 'apple'> = ['google', 'microsoft', 'github', 'apple'];
const roles: Array<'owner' | 'admin' | 'analyst' | 'developer' | 'auditor'> = ['owner', 'admin', 'analyst', 'developer', 'auditor'];

export function AccountWorkspaceClient() {
  const [customer, setCustomer] = useState<CustomerSummary | null>(null);
  const [session, setSession] = useState<CustomerSession | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationRecord[]>([]);
  const [quota, setQuota] = useState<QuotaResponse['quota'] | null>(null);
  const [usageRecords, setUsageRecords] = useState<QuotaResponse['usageRecords']>([]);
  const [organizationUsage, setOrganizationUsage] = useState<OrgUsageSummary | null>(null);
  const [organizationAudit, setOrganizationAudit] = useState<OrgAuditSummary | null>(null);
  const [organizationLedgerLoading, setOrganizationLedgerLoading] = useState(false);
  const [coriAlphaSummary, setCoriAlphaSummary] = useState<CoriAlphaWorkspaceSummary | null>(null);
  const [coriAlphaLoading, setCoriAlphaLoading] = useState(false);
  const [organizationName, setOrganizationName] = useState('');
  const [billingContactEmail, setBillingContactEmail] = useState('');
  const [domain, setDomain] = useState('');
  const [memberCustomerId, setMemberCustomerId] = useState('');
  const [memberRole, setMemberRole] = useState<'owner' | 'admin' | 'analyst' | 'developer' | 'auditor'>('developer');
  const [selectedOrganizationId, setSelectedOrganizationId] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedOrganization = useMemo(
    () => organizations.find((organization) => organization.id === selectedOrganizationId) ?? organizations[0] ?? null,
    [organizations, selectedOrganizationId],
  );
  const activeOrganizationId = useMemo(
    () => selectedOrganization?.id ?? customer?.organizationId ?? null,
    [customer?.organizationId, selectedOrganization?.id],
  );

  useEffect(() => {
    const load = async () => {
      const [meRes, orgRes, quotaRes] = await Promise.all([
        fetch('/api/customer/me'),
        fetch('/api/organizations'),
        fetch('/api/customers/quota'),
      ]);

      let nextSelectedOrganizationId = '';
      if (meRes.ok) {
        const meBody = (await meRes.json()) as { customer?: CustomerSummary; session?: CustomerSession };
        if (meBody.customer) {
          setCustomer(meBody.customer);
          setSession(meBody.session ?? null);
          setBillingContactEmail(meBody.customer.email);
          setMemberCustomerId(meBody.customer.id);
          nextSelectedOrganizationId = meBody.customer.organizationId ?? '';
          setOrganizationName(meBody.customer.organizationId ? meBody.customer.organizationId.replace(/^org_/, '').replace(/-/g, ' ') : '');
        }
      }
      if (orgRes.ok) {
        const orgBody = (await orgRes.json()) as { organizations?: OrganizationRecord[] };
        setOrganizations(orgBody.organizations ?? []);
        if (!nextSelectedOrganizationId && orgBody.organizations?.[0]) {
          nextSelectedOrganizationId = orgBody.organizations[0].id;
        }
      }

      if (quotaRes.ok) {
        const quotaBody = (await quotaRes.json()) as QuotaResponse;
        setQuota(quotaBody.quota);
        setUsageRecords(quotaBody.usageRecords ?? []);
      }

      if (nextSelectedOrganizationId) {
        setSelectedOrganizationId(nextSelectedOrganizationId);
      }
    };

    void load().catch((caught) => {
      setError(caught instanceof Error ? caught.message : String(caught));
    });
  }, []);

  useEffect(() => {
    let active = true;

    const loadCoriAlphaSummary = async () => {
      setCoriAlphaLoading(true);
      try {
        const response = await fetch('/api/cori-alpha/summary');
        const payload = (await response.json().catch(() => null)) as { surface?: CoriAlphaWorkspaceSummary; error?: string } | null;
        if (!active) {
          return;
        }
        if (response.ok && payload?.surface) {
          setCoriAlphaSummary(payload.surface);
        } else {
          setCoriAlphaSummary(null);
        }
      } finally {
        if (active) {
          setCoriAlphaLoading(false);
        }
      }
    };

    void loadCoriAlphaSummary().catch((caught) => {
      if (!active) {
        return;
      }
      setError(caught instanceof Error ? caught.message : String(caught));
      setCoriAlphaSummary(null);
      setCoriAlphaLoading(false);
    });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!activeOrganizationId) {
      setOrganizationUsage(null);
      setOrganizationAudit(null);
      setOrganizationLedgerLoading(false);
      return;
    }

    const loadOrganizationLedger = async () => {
      setOrganizationLedgerLoading(true);
      try {
        const [usageRes, pricingRes, routingRes, entitlementsRes] = await Promise.all([
          fetch(`/api/organizations/${encodeURIComponent(activeOrganizationId)}/usage`),
          fetch(`/api/organizations/${encodeURIComponent(activeOrganizationId)}/audit/pricing`),
          fetch(`/api/organizations/${encodeURIComponent(activeOrganizationId)}/audit/routing`),
          fetch(`/api/organizations/${encodeURIComponent(activeOrganizationId)}/audit/entitlements`),
        ]);

        if (usageRes.ok) {
          setOrganizationUsage((await usageRes.json()) as OrgUsageSummary);
        } else {
          setOrganizationUsage(null);
        }

        setOrganizationAudit({
          pricing: pricingRes.ok ? (((await pricingRes.json()) as { audit?: unknown[] }).audit ?? []) : [],
          routing: routingRes.ok ? (((await routingRes.json()) as { audit?: unknown[] }).audit ?? []) : [],
          entitlements: entitlementsRes.ok ? (((await entitlementsRes.json()) as { audit?: unknown[] }).audit ?? []) : [],
        });
      } finally {
        setOrganizationLedgerLoading(false);
      }
    };

    void loadOrganizationLedger().catch((caught) => {
      setError(caught instanceof Error ? caught.message : String(caught));
      setOrganizationUsage(null);
      setOrganizationAudit(null);
      setOrganizationLedgerLoading(false);
    });
  }, [activeOrganizationId]);

  async function startOAuth(provider: (typeof oauthProviders)[number], mode: 'login' | 'signup') {
    setError(null);
    setMessage(null);
    window.location.href = `/api/auth/oauth/${provider}/start?mode=${mode}&returnTo=/account`;
  }

  async function createOrganization(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    const res = await fetch('/api/organizations', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        name: organizationName,
        billingContactEmail,
        planId: session?.planId ?? customer?.planId ?? 'free',
        domain: domain || undefined,
        ownerRole: 'owner',
      }),
    });
    const body = (await res.json().catch(() => ({}))) as { organization?: OrganizationRecord; error?: string };
    if (!res.ok || !body.organization) {
      throw new Error(body.error ?? 'organization creation failed');
    }
    setOrganizations((current) => [body.organization!, ...current.filter((organization) => organization.id !== body.organization?.id)]);
    setSelectedOrganizationId(body.organization.id);
    setMessage(`Created organization ${body.organization.name}`);
  }

  async function addMember(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedOrganization) {
      setError('Select an organization first.');
      return;
    }
    setError(null);
    setMessage(null);
    const res = await fetch(`/api/organizations/${selectedOrganization.id}/members`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        customerId: memberCustomerId,
        role: memberRole,
      }),
    });
    const body = (await res.json().catch(() => ({}))) as { organization?: OrganizationRecord; error?: string };
    if (!res.ok || !body.organization) {
      throw new Error(body.error ?? 'member update failed');
    }
    setOrganizations((current) => current.map((organization) => (organization.id === body.organization?.id ? body.organization! : organization)));
    setMessage(`Updated role for ${memberCustomerId} on ${body.organization.name}`);
  }

  return (
    <div style={layoutStyle}>
      <section style={heroCardStyle}>
        <div style={eyebrowStyle}>Customer identity spine</div>
        <h1 style={titleStyle}>OAuth, org accounts, RBAC, and quota enforcement in one place</h1>
        <p style={ledeStyle}>
          Use Google, Microsoft, GitHub, or Apple sign-in to create a signed customer session, then manage organizations, roles, and entitlement-backed usage from the same workspace.
        </p>
        <div style={buttonRowStyle}>
          {oauthProviders.map((provider) => (
            <div key={provider} style={providerCardStyle}>
              <strong>{provider}</strong>
              <div style={providerButtonsStyle}>
                <button style={secondaryButtonStyle} type="button" onClick={() => void startOAuth(provider, 'login')}>
                  Log in
                </button>
                <button style={primaryButtonStyle} type="button" onClick={() => void startOAuth(provider, 'signup')}>
                  Sign up
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div style={gridStyle}>
        <section style={cardStyle}>
          <h2 style={headingStyle}>Current customer</h2>
          {customer ? (
            <>
              <p style={heroValueStyle}>{customer.planName}</p>
              <p style={subtleStyle}>{customer.email}</p>
              <div style={metricGridStyle}>
                <Metric label="Provider" value={customer.authProvider} />
                <Metric label="Role" value={customer.organizationRole ?? 'none'} />
                <Metric label="Audit scope" value={customer.entitlements.auditScope} />
                <Metric label="Routing tier" value={customer.entitlements.routingTier} />
              </div>
              <p style={subtleStyle}>Session {session?.sessionId ?? 'not loaded'} | Org {customer.organizationId ?? 'none'}</p>
            </>
          ) : (
            <p style={subtleStyle}>Log in with one of the OAuth providers to populate the customer identity and RBAC surface.</p>
          )}
        </section>

        <QuotaSummary
          title="Quota and overage"
          quota={quota}
          usageRecordCount={usageRecords.length}
          emptyMessage="Quota reporting appears here after the first authenticated request."
        />
      </div>

      <OrgLedgerSummary
        organizationId={activeOrganizationId}
        loading={organizationLedgerLoading}
        usage={organizationUsage}
        audit={organizationAudit}
        emptyMessage="Select or create an organization to see the shared org ledger summary here."
      />

      <CoriAlphaSummaryCard
        summary={coriAlphaSummary}
        loading={coriAlphaLoading}
        title="CORI Alpha upload intelligence"
        surfaceLabel="Customer workspace view"
        emptyMessage="CORI Alpha upload intelligence appears here once the local ledger has at least one governed upload."
      />

      <div style={gridStyle}>
        <section style={cardStyle}>
          <h2 style={headingStyle}>Organization management</h2>
          <form onSubmit={(event) => void createOrganization(event)} style={formStyle}>
            <input placeholder="Organization name" value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} style={inputStyle} />
            <input placeholder="Billing contact email" value={billingContactEmail} onChange={(event) => setBillingContactEmail(event.target.value)} style={inputStyle} />
            <input placeholder="Domain (optional)" value={domain} onChange={(event) => setDomain(event.target.value)} style={inputStyle} />
            <button type="submit" style={primaryButtonStyle}>Create organization</button>
          </form>
          <div style={{ marginTop: 16 }}>
            <label style={labelStyle}>Selected organization</label>
            <select value={selectedOrganizationId} onChange={(event) => setSelectedOrganizationId(event.target.value)} style={inputStyle}>
              {organizations.map((organization) => (
                <option key={organization.id} value={organization.id}>{organization.name}</option>
              ))}
            </select>
          </div>
          {selectedOrganization ? (
            <div style={{ marginTop: 16 }}>
              <p style={subtleStyle}>Owner {selectedOrganization.ownerCustomerId} | Billing {selectedOrganization.billingContactEmail}</p>
              <p style={subtleStyle}>Members {selectedOrganization.members.length}</p>
            </div>
          ) : (
            <p style={subtleStyle}>Create or select an organization to manage membership and roles.</p>
          )}
        </section>

        <section style={cardStyle}>
          <h2 style={headingStyle}>RBAC management</h2>
          <form onSubmit={(event) => void addMember(event)} style={formStyle}>
            <input placeholder="Customer id" value={memberCustomerId} onChange={(event) => setMemberCustomerId(event.target.value)} style={inputStyle} />
            <select value={memberRole} onChange={(event) => setMemberRole(event.target.value as typeof memberRole)} style={inputStyle}>
              {roles.map((role) => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
            <button type="submit" style={primaryButtonStyle} disabled={!selectedOrganization}>Update role</button>
          </form>
          <div style={{ marginTop: 16, overflowX: 'auto' }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Organization</th>
                  <th style={thStyle}>Owner</th>
                  <th style={thStyle}>Members</th>
                  <th style={thStyle}>Roles</th>
                </tr>
              </thead>
              <tbody>
                {organizations.map((organization) => (
                  <tr key={organization.id}>
                    <td style={tdStyle}>{organization.name}</td>
                    <td style={tdStyle}>{organization.ownerCustomerId}</td>
                    <td style={tdStyle}>{organization.members.length}</td>
                    <td style={tdStyle}>{organization.members.map((member) => member.role).join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      {message ? <p style={successStyle}>{message}</p> : null}
      {error ? <p style={errorStyle}>{error}</p> : null}
    </div>
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

const layoutStyle: React.CSSProperties = {
  display: 'grid',
  gap: 24,
};

const heroCardStyle: React.CSSProperties = {
  borderRadius: 28,
  padding: 28,
  background: 'linear-gradient(145deg, rgba(15, 118, 110, 0.12), rgba(2, 132, 199, 0.08)), rgba(255,255,255,0.9)',
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
  maxWidth: 900,
  margin: '14px 0 0',
  color: '#475569',
  lineHeight: 1.7,
};

const buttonRowStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
  marginTop: 24,
};

const providerCardStyle: React.CSSProperties = {
  borderRadius: 20,
  padding: 16,
  border: '1px solid rgba(15, 23, 42, 0.08)',
  background: 'rgba(255,255,255,0.8)',
};

const providerButtonsStyle: React.CSSProperties = {
  display: 'flex',
  gap: 8,
  marginTop: 10,
  flexWrap: 'wrap',
};

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
  gap: 20,
};

const cardStyle: React.CSSProperties = {
  borderRadius: 24,
  padding: 24,
  background: 'rgba(255,255,255,0.88)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  boxShadow: '0 18px 42px rgba(15, 23, 42, 0.05)',
};

const headingStyle: React.CSSProperties = {
  marginTop: 0,
  marginBottom: 12,
  fontSize: '1.4rem',
};

const subtleStyle: React.CSSProperties = {
  color: '#475569',
  lineHeight: 1.7,
};

const heroValueStyle: React.CSSProperties = {
  fontSize: '2rem',
  fontWeight: 800,
  margin: '0 0 6px',
};

const metricGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 10,
  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
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

const formStyle: React.CSSProperties = {
  display: 'grid',
  gap: 10,
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px 14px',
  borderRadius: 12,
  border: '1px solid #cbd5e1',
  background: '#fff',
  color: '#0f172a',
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  marginBottom: 6,
  color: '#475569',
  fontSize: 13,
};

const primaryButtonStyle: React.CSSProperties = {
  border: 'none',
  borderRadius: 12,
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
};

const successStyle: React.CSSProperties = {
  color: '#166534',
  fontWeight: 700,
};

const errorStyle: React.CSSProperties = {
  color: '#b91c1c',
  fontWeight: 700,
};
