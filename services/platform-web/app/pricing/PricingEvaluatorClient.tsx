'use client';

import { useEffect, useMemo, useState } from 'react';

import {
  DEFAULT_PRICING_INPUT,
  type PublicPricingEvaluationResponse,
} from '../../lib/pricing';
import type {
  CustomerRecord,
  CustomerSession,
  CustomerPlanId,
} from '@aaes-os/platform-core';
import type { SovereignRouterXPricingInput } from '@aaes-os/sovereignx-router';

type PricingResponse = PublicPricingEvaluationResponse & {
  handoff?: {
    persisted: boolean;
    ledgerPath: string | null;
  };
  cep?: {
    published: boolean;
    promotionRequestId?: string;
    replayJobId?: string;
    decisionId?: string;
    viewState?: {
      selectedKind: 'promotion-request' | 'replay-job' | 'decision';
      selectedArtifactId: string | null;
      updatedAt: string;
      source: 'local' | 'remote';
    };
    error?: string;
  };
  auditSurface?: {
    signer: string;
    signed_at: string;
    signature: string;
    surface: {
      customerId: string;
      organizationId?: string;
      organizationRole?: string;
      planId: string;
      planName: string;
      generatedAt: string;
      requestId: string;
      routingJustification: string;
      pricingJustification: string;
      entitlements: {
        routingTier: string;
        governanceLevel: string;
        auditScope: string;
        customerAuditSurfaces: boolean;
        overageBillingEnabled: boolean;
      };
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
      treasury: {
        grossInvoiceUsd: number;
        openAiUsageCostUsd: number;
        taxReserveUsd: number;
        platformReserveUsd: number;
        ownerProfitUsd: number;
      };
      pricingPlan: {
        strategy: string;
        packaging: string;
        targetMarginBand: string;
      };
    };
  };
};

type CustomerAccountResponse = {
  customer: CustomerRecord;
  session: CustomerSession;
};

type CustomerPricingForm = SovereignRouterXPricingInput & {
  customerInvoiceUsd?: number;
  openAiUsageCostUsd?: number;
  taxRatePct?: number;
  profitReservePct?: number;
  platformReservePct?: number;
};

const segmentOptions: SovereignRouterXPricingInput['segment'][] = [
  'Individual',
  'Professional',
  'Team',
  'Enterprise',
  'Public Sector',
];

const planOptions: CustomerPlanId[] = ['free', 'pro', 'enterprise'];
const authProviders: Array<'email' | 'google' | 'microsoft' | 'github' | 'apple'> = [
  'email',
  'google',
  'microsoft',
  'github',
  'apple',
];

export function PricingEvaluatorClient() {
  const [email, setEmail] = useState('customer@example.com');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('Customer');
  const [organizationName, setOrganizationName] = useState('');
  const [organizationId, setOrganizationId] = useState('');
  const [organizationRole, setOrganizationRole] = useState<'owner' | 'admin' | 'analyst' | 'developer' | 'auditor'>('owner');
  const [authProvider, setAuthProvider] = useState<'email' | 'google' | 'microsoft' | 'github' | 'apple'>('email');
  const [authSubject, setAuthSubject] = useState('');
  const [governanceProfile, setGovernanceProfile] = useState<'strict' | 'balanced' | 'experimental'>('balanced');
  const [planId, setPlanId] = useState<CustomerPlanId>('free');
  const [session, setSession] = useState<CustomerSession | null>(null);
  const [customer, setCustomer] = useState<CustomerRecord | null>(null);
  const [form, setForm] = useState<CustomerPricingForm>(DEFAULT_PRICING_INPUT);
  const [response, setResponse] = useState<PricingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [accountMessage, setAccountMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSigningUp, setIsSigningUp] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const matrix = useMemo(() => response?.evaluation.strategyScenarios ?? [], [response]);

  useEffect(() => {
    const loadCustomer = async () => {
      try {
        const res = await fetch('/api/customer/me');
        if (!res.ok) {
          return;
        }
        const body = (await res.json()) as CustomerAccountResponse | { error?: string };
        if ('customer' in body && 'session' in body) {
          setSession(body.session);
          setCustomer(body.customer);
          setEmail(body.customer.email);
          setDisplayName(body.customer.displayName ?? body.customer.email);
          setPlanId(body.customer.planId);
          setAuthProvider(body.customer.authProvider);
          setAuthSubject(body.customer.authSubject ?? '');
          setOrganizationName(body.customer.organizationId ?? '');
          setOrganizationId(body.customer.organizationId ?? '');
          setOrganizationRole(body.session.organizationRole ?? 'owner');
          setGovernanceProfile(body.session.governanceProfile);
        }
      } catch {
        // Ignore unauthenticated reloads.
      }
    };

    void loadCustomer();
  }, []);

  function updateField<K extends keyof CustomerPricingForm>(key: K, value: CustomerPricingForm[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function signup(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAccountMessage(null);
    setError(null);
    setIsSigningUp(true);
    try {
      const res = await fetch('/api/customer/signup', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          email,
          password: password || undefined,
          displayName,
          authProvider,
          authSubject: authSubject || undefined,
          planId,
          organizationId: organizationId || undefined,
          organizationName: organizationName || undefined,
          organizationRole,
          governanceProfile,
        }),
      });
      const body = (await res.json()) as CustomerAccountResponse & { error?: string };
      if (!res.ok || !body.session) {
        throw new Error(body.error ?? `Signup failed with HTTP ${res.status}`);
      }
      setSession(body.session);
      setCustomer(body.customer);
      setAccountMessage(`Created ${body.customer.email} on the ${body.customer.planName} plan`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setIsSigningUp(false);
    }
  }

  async function login(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAccountMessage(null);
    setError(null);
    setIsLoggingIn(true);
    try {
      const res = await fetch('/api/customer/login', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          email,
          password: password || undefined,
          authProvider,
          authSubject: authSubject || undefined,
          governanceProfile,
        }),
      });
      const body = (await res.json()) as CustomerAccountResponse & { error?: string };
      if (!res.ok || !body.session) {
        throw new Error(body.error ?? `Login failed with HTTP ${res.status}`);
      }
      setSession(body.session);
      setCustomer(body.customer);
      setAccountMessage(`Authenticated as ${body.customer.email} on ${body.customer.planName}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setIsLoggingIn(false);
    }
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      setError('Log in or sign up first to run a customer-authenticated evaluation.');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      const res = await fetch('/api/customer/pricing/evaluate', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ governanceProfile, ...form }),
      });
      const body = (await res.json()) as PricingResponse | { error?: string };
      if (!res.ok || !('evaluation' in body)) {
        throw new Error(body && 'error' in body && body.error ? body.error : `Pricing evaluation failed with HTTP ${res.status}`);
      }
      setResponse(body);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div style={layoutStyle}>
      <form onSubmit={signup} style={cardStyle}>
        <h2 style={headingStyle}>Create account</h2>
        <p style={subtleStyle}>Set up a customer identity, assign a plan, and issue the cookie-backed session that powers pricing, routing, and treasury.</p>
        <div style={fieldGridStyle}>
          <Field label="Email">
            <input value={email} onChange={(event) => setEmail(event.target.value)} style={inputStyle} />
          </Field>
          <Field label="Password">
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} style={inputStyle} />
          </Field>
          <Field label="Display name">
            <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} style={inputStyle} />
          </Field>
          <Field label="Plan">
            <select value={planId} onChange={(event) => setPlanId(event.target.value as CustomerPlanId)} style={inputStyle}>
              {planOptions.map((plan) => (
                <option key={plan} value={plan}>{plan}</option>
              ))}
            </select>
          </Field>
          <Field label="Organization name">
            <input value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} style={inputStyle} />
          </Field>
          <Field label="Organization id">
            <input value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} style={inputStyle} />
          </Field>
          <Field label="Organization role">
            <select value={organizationRole} onChange={(event) => setOrganizationRole(event.target.value as typeof organizationRole)} style={inputStyle}>
              <option value="owner">owner</option>
              <option value="admin">admin</option>
              <option value="analyst">analyst</option>
              <option value="developer">developer</option>
              <option value="auditor">auditor</option>
            </select>
          </Field>
          <Field label="Auth provider">
            <select value={authProvider} onChange={(event) => setAuthProvider(event.target.value as typeof authProvider)} style={inputStyle}>
              {authProviders.map((provider) => (
                <option key={provider} value={provider}>{provider}</option>
              ))}
            </select>
          </Field>
          <Field label="OAuth subject">
            <input value={authSubject} onChange={(event) => setAuthSubject(event.target.value)} style={inputStyle} />
          </Field>
          <Field label="Governance profile">
            <select value={governanceProfile} onChange={(event) => setGovernanceProfile(event.target.value as typeof governanceProfile)} style={inputStyle}>
              <option value="balanced">balanced</option>
              <option value="strict">strict</option>
              <option value="experimental">experimental</option>
            </select>
          </Field>
        </div>
        <button type="submit" style={buttonStyle} disabled={isSigningUp}>
          {isSigningUp ? 'Creating account...' : 'Create account'}
        </button>
        {accountMessage ? <p style={successStyle}>{accountMessage}</p> : null}
      </form>

      <form onSubmit={login} style={cardStyle}>
        <h2 style={headingStyle}>Customer access</h2>
          <p style={subtleStyle}>Use email/password or OAuth-style identity to refresh the signed customer session.</p>
        <div style={fieldGridStyle}>
          <Field label="Email">
            <input value={email} onChange={(event) => setEmail(event.target.value)} style={inputStyle} />
          </Field>
          <Field label="Password">
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} style={inputStyle} />
          </Field>
          <Field label="Auth provider">
            <select value={authProvider} onChange={(event) => setAuthProvider(event.target.value as typeof authProvider)} style={inputStyle}>
              {authProviders.map((provider) => (
                <option key={provider} value={provider}>{provider}</option>
              ))}
            </select>
          </Field>
          <Field label="OAuth subject">
            <input value={authSubject} onChange={(event) => setAuthSubject(event.target.value)} style={inputStyle} />
          </Field>
          <Field label="Governance profile">
            <select value={governanceProfile} onChange={(event) => setGovernanceProfile(event.target.value as typeof governanceProfile)} style={inputStyle}>
              <option value="balanced">balanced</option>
              <option value="strict">strict</option>
              <option value="experimental">experimental</option>
            </select>
          </Field>
        </div>
        <button type="submit" style={buttonStyle} disabled={isLoggingIn}>
          {isLoggingIn ? 'Authenticating...' : session ? 'Refresh Session' : 'Log In'}
        </button>
        {session ? <p style={successStyle}>Session {session.sessionId} active for {session.planName}</p> : null}
        {accountMessage ? <p style={successStyle}>{accountMessage}</p> : null}
      </form>

      <form onSubmit={submit} style={cardStyle}>
        <h2 style={headingStyle}>Evaluate the plan</h2>
        <p style={subtleStyle}>The request is authenticated through the customer session cookie, routed through Sovereign Router X, and written to the handoff ledger when signing is enabled.</p>
        <div style={fieldGridStyle}>
          <Field label="Segment">
            <select value={form.segment} onChange={(event) => updateField('segment', event.target.value as SovereignRouterXPricingInput['segment'])} style={inputStyle}>
              {segmentOptions.map((segment) => (
                <option key={segment} value={segment}>{segment}</option>
              ))}
            </select>
          </Field>
          <Field label="Monthly customers">
            <input type="number" min={1} value={form.monthlyCustomers} onChange={(event) => updateField('monthlyCustomers', Number(event.target.value))} style={inputStyle} />
          </Field>
          <Field label="Routed requests / customer">
            <input type="number" min={1} value={form.routedRequestsPerCustomer} onChange={(event) => updateField('routedRequestsPerCustomer', Number(event.target.value))} style={inputStyle} />
          </Field>
          <Field label="Governance reviews / customer">
            <input type="number" min={0} value={form.governanceReviewsPerCustomer} onChange={(event) => updateField('governanceReviewsPerCustomer', Number(event.target.value))} style={inputStyle} />
          </Field>
          <Field label="Knowledge updates / customer">
            <input type="number" min={0} value={form.knowledgeUpdatesPerCustomer} onChange={(event) => updateField('knowledgeUpdatesPerCustomer', Number(event.target.value))} style={inputStyle} />
          </Field>
          <Field label="Service hours / customer">
            <input type="number" min={0} step="0.25" value={form.serviceHoursPerCustomer} onChange={(event) => updateField('serviceHoursPerCustomer', Number(event.target.value))} style={inputStyle} />
          </Field>
          <Field label="Compliance pressure">
            <input type="range" min={0} max={100} value={form.compliancePressure} onChange={(event) => updateField('compliancePressure', Number(event.target.value))} style={rangeStyle} />
            <span style={rangeValueStyle}>{form.compliancePressure}</span>
          </Field>
          <Field label="Workload volatility">
            <input type="range" min={0} max={100} value={form.workloadVolatility} onChange={(event) => updateField('workloadVolatility', Number(event.target.value))} style={rangeStyle} />
            <span style={rangeValueStyle}>{form.workloadVolatility}</span>
          </Field>
          <Field label="Support complexity">
            <input type="range" min={0} max={100} value={form.supportComplexity} onChange={(event) => updateField('supportComplexity', Number(event.target.value))} style={rangeStyle} />
            <span style={rangeValueStyle}>{form.supportComplexity}</span>
          </Field>
          <Field label="Invoice amount">
            <input type="number" min={0} step="0.01" value={form.customerInvoiceUsd ?? ''} onChange={(event) => updateField('customerInvoiceUsd', Number(event.target.value))} style={inputStyle} />
          </Field>
          <Field label="OpenAI usage cost">
            <input type="number" min={0} step="0.01" value={form.openAiUsageCostUsd ?? ''} onChange={(event) => updateField('openAiUsageCostUsd', Number(event.target.value))} style={inputStyle} />
          </Field>
        </div>
        <label style={toggleStyle}>
          <input type="checkbox" checked={form.privateDeployment} onChange={(event) => updateField('privateDeployment', event.target.checked)} />
          Private deployment
        </label>
        <label style={toggleStyle}>
          <input type="checkbox" checked={form.assuranceRequired} onChange={(event) => updateField('assuranceRequired', event.target.checked)} />
          Assurance required
        </label>
        <button type="submit" style={buttonStyle} disabled={isSubmitting || !session}>
          {isSubmitting ? 'Evaluating...' : 'Run Sovereign Router X'}
        </button>
        {error ? <p style={errorStyle}>{error}</p> : null}
      </form>

      <div style={stackStyle}>
        <section style={cardStyle}>
          <h2 style={headingStyle}>Recommended plan</h2>
          {response ? (
            <>
              <p style={heroValueStyle}>{response.evaluation.recommendedScenario.strategy}</p>
              <p style={subtleStyle}>{response.evaluation.recommendedScenario.packaging}</p>
              <div style={metricGridStyle}>
                <Metric label="Revenue" value={formatCurrency(response.evaluation.economics.monthlyRevenueUsd)} />
                <Metric label="Direct cost" value={formatCurrency(response.evaluation.economics.monthlyDirectCostUsd)} />
                <Metric label="Gross margin" value={`${formatCurrency(response.evaluation.economics.grossMarginUsd)} (${response.evaluation.economics.grossMarginPct.toFixed(1)}%)`} />
                <Metric label="Model" value={`${response.evaluation.routing.modelDecision.model} / ${response.evaluation.routing.backend}`} />
              </div>
              <p style={subtleStyle}>Ledger {response.ledger.persisted ? 'written to ops-console' : 'not persisted'} {response.ledger.url ? `at ${response.ledger.url}` : ''}</p>
              <p style={subtleStyle}>Handoff {response.handoff?.persisted ? `saved to ${response.handoff.ledgerPath}` : 'not recorded'}</p>
              <p style={subtleStyle}>CEP {response.cep?.published ? `published as ${response.cep.decisionId ?? 'decision bundle'}` : response.cep?.error ? `publish failed: ${response.cep.error}` : 'not published'}</p>
              {response.cep?.viewState ? <p style={subtleStyle}>CEP view state {response.cep.viewState.selectedKind} / {response.cep.viewState.selectedArtifactId ?? 'none'}</p> : null}
              {response.auditSurface ? <p style={subtleStyle}>Signed audit surface {response.auditSurface.signature.slice(0, 12)}… for routing and pricing justification</p> : null}
            </>
          ) : (
            <p style={subtleStyle}>Authenticate and run an evaluation to see the recommended plan, routed model, and ledger handoff.</p>
          )}
        </section>

        <section style={cardStyle}>
          <h2 style={headingStyle}>Customer profile</h2>
          {customer ? (
            <>
              <p style={heroValueStyle}>{customer.planName}</p>
              <div style={metricGridStyle}>
                <Metric label="Customer" value={customer.email} />
                <Metric label="Plan" value={customer.planId} />
                <Metric label="Audit scope" value={customer.entitlements.auditScope} />
                <Metric label="Routing tier" value={customer.entitlements.routingTier} />
              </div>
              <p style={subtleStyle}>Handoff {customer.entitlements.codexPacketHandoff ? 'enabled' : 'disabled'} | ledger {customer.entitlements.usageLedger ? 'enabled' : 'disabled'} | margin dashboard {customer.entitlements.marginDashboard ? 'enabled' : 'disabled'}</p>
              <p style={subtleStyle}>Organization {customer.organizationId ?? 'none'} | role {customer.organizationRole ?? 'none'}</p>
            </>
          ) : (
            <p style={subtleStyle}>Create or refresh an account to see customer identity, plan assignment, and entitlements.</p>
          )}
        </section>

        <section style={cardStyle}>
          <h2 style={headingStyle}>Signed audit surface</h2>
          {response?.auditSurface ? (
            <>
              <div style={metricGridStyle}>
                <Metric label="Signer" value={response.auditSurface.signer} />
                <Metric label="Plan" value={response.auditSurface.surface.planName} />
                <Metric label="Quota" value={`${response.auditSurface.surface.quota.requestCount}/${response.auditSurface.surface.quota.requestLimit}`} />
                <Metric label="Overage" value={formatCurrency(response.auditSurface.surface.quota.overageBillingUsd)} />
              </div>
              <p style={subtleStyle}>Quota status: {response.auditSurface.surface.quota.enforcement.status} | allowed: {response.auditSurface.surface.quota.enforcement.allowed ? 'yes' : 'no'}</p>
              <p style={subtleStyle}>{response.auditSurface.surface.routingJustification}</p>
              <p style={subtleStyle}>{response.auditSurface.surface.pricingJustification}</p>
              <pre style={codeStyle}>{JSON.stringify(response.auditSurface, null, 2)}</pre>
            </>
          ) : (
            <p style={subtleStyle}>The signed audit surface appears after evaluation and includes routing and pricing justification.</p>
          )}
        </section>

        <section style={cardStyle}>
          <h2 style={headingStyle}>Codex packet</h2>
          {response ? (
            <pre style={codeStyle}>{JSON.stringify(response.evaluation.requestPacket, null, 2)}</pre>
          ) : (
            <p style={subtleStyle}>The packet preview appears here after evaluation.</p>
          )}
        </section>

        <section style={cardStyle}>
          <h2 style={headingStyle}>Scenario matrix</h2>
          {response ? (
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Strategy</th>
                  <th style={thStyle}>Score</th>
                  <th style={thStyle}>Margin</th>
                  <th style={thStyle}>Packaging</th>
                </tr>
              </thead>
              <tbody>
                {matrix.map((scenario) => (
                  <tr key={scenario.strategy}>
                    <td style={tdStyle}>{scenario.strategy}</td>
                    <td style={tdStyle}>{scenario.score.toFixed(1)}</td>
                    <td style={tdStyle}>{scenario.estimatedGrossMarginPct.toFixed(1)}%</td>
                    <td style={tdStyle}>{scenario.packaging}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={subtleStyle}>The comparison matrix fills in after the first run.</p>
          )}
        </section>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={fieldStyle}>
      <span style={labelStyle}>{label}</span>
      {children}
    </label>
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

const layoutStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
  gap: 24,
  alignItems: 'start',
};

const stackStyle: React.CSSProperties = {
  display: 'grid',
  gap: 16,
};

const cardStyle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.92)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  borderRadius: 24,
  padding: 24,
  boxShadow: '0 24px 80px rgba(15, 23, 42, 0.08)',
  backdropFilter: 'blur(10px)',
};

const headingStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 26,
  letterSpacing: '-0.03em',
};

const subtleStyle: React.CSSProperties = {
  marginTop: 8,
  marginBottom: 0,
  color: '#4b5563',
  lineHeight: 1.55,
};

const fieldGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 14,
  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
  marginTop: 20,
};

const fieldStyle: React.CSSProperties = {
  display: 'grid',
  gap: 8,
};

const labelStyle: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  color: '#374151',
};

const inputStyle: React.CSSProperties = {
  borderRadius: 14,
  border: '1px solid #d1d5db',
  padding: '12px 14px',
  fontSize: 14,
  background: '#fff',
};

const rangeStyle: React.CSSProperties = {
  width: '100%',
};

const rangeValueStyle: React.CSSProperties = {
  fontSize: 13,
  color: '#0f172a',
  fontWeight: 600,
};

const toggleStyle: React.CSSProperties = {
  display: 'flex',
  gap: 10,
  alignItems: 'center',
  marginTop: 14,
  fontSize: 14,
  color: '#0f172a',
};

const buttonStyle: React.CSSProperties = {
  marginTop: 20,
  border: 'none',
  borderRadius: 16,
  padding: '14px 18px',
  background: 'linear-gradient(135deg, #0f172a, #0f766e)',
  color: '#fff',
  fontWeight: 700,
  cursor: 'pointer',
  width: '100%',
};

const errorStyle: React.CSSProperties = {
  marginTop: 12,
  color: '#b91c1c',
};

const successStyle: React.CSSProperties = {
  marginTop: 12,
  color: '#065f46',
};

const heroValueStyle: React.CSSProperties = {
  margin: '8px 0 0',
  fontSize: 28,
  fontWeight: 800,
  letterSpacing: '-0.04em',
  color: '#0f172a',
};

const metricGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
  gap: 12,
  marginTop: 18,
};

const metricStyle: React.CSSProperties = {
  borderRadius: 16,
  padding: 14,
  background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.03), rgba(15, 118, 110, 0.04))',
  border: '1px solid rgba(15, 23, 42, 0.06)',
};

const metricLabelStyle: React.CSSProperties = {
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  color: '#6b7280',
  marginBottom: 6,
};

const metricValueStyle: React.CSSProperties = {
  fontSize: 16,
  fontWeight: 700,
  color: '#0f172a',
};

const codeStyle: React.CSSProperties = {
  margin: 0,
  padding: 16,
  background: '#0f172a',
  color: '#d1fae5',
  borderRadius: 16,
  overflow: 'auto',
  fontSize: 13,
  lineHeight: 1.5,
};

const tableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
};

const thStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '10px 8px',
  borderBottom: '1px solid #e5e7eb',
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  color: '#6b7280',
};

const tdStyle: React.CSSProperties = {
  padding: '12px 8px',
  borderBottom: '1px solid #eef2f7',
  verticalAlign: 'top',
  fontSize: 14,
};
