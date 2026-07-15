import { describe, expect, it } from 'vitest';

import { createApp } from './server.js';
import { platform } from './state.js';

describe('platform-api', () => {
  it('creates app with health route', async () => {
    const app = createApp();
    expect(app).toBeTruthy();

    const server = app.listen(0);
    const address = server.address();
    const port = typeof address === 'object' && address ? address.port : 0;

    const res = await fetch(`http://127.0.0.1:${port}/health`);
    expect(res.status).toBe(200);
    const body = (await res.json()) as { status: string };
    expect(body.status).toBe('ok');

    server.close();
    expect(platform.listProfiles()).toHaveLength(3);
  });

  it('signs up customers, issues sessions, and exposes customer identity and entitlements', async () => {
    const app = createApp();
    const server = app.listen(0);
    const address = server.address();
    const port = typeof address === 'object' && address ? address.port : 0;

    try {
      const signup = await fetch(`http://127.0.0.1:${port}/v1/customers/signup`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          email: 'customer@example.com',
          password: 'secret-123',
          displayName: 'Customer One',
          planId: 'pro',
          organizationName: 'Customer One Org',
          organizationRole: 'owner',
          governanceProfile: 'balanced',
        }),
      });
      expect(signup.status).toBe(201);
      const signupBody = (await signup.json()) as {
        customer: { email: string; planId: string; entitlements: { codexPacketHandoff: boolean }; organizationId?: string; organizationRole?: string };
        session: { sessionId: string };
      };
      expect(signupBody.customer.email).toBe('customer@example.com');
      expect(signupBody.customer.planId).toBe('pro');
      expect(signupBody.customer.entitlements.codexPacketHandoff).toBe(true);
      expect(signupBody.customer.organizationId).toBeTruthy();
      expect(signupBody.customer.organizationRole).toBe('owner');
      expect(signupBody.session.sessionId).toBeTruthy();

      const me = await fetch(`http://127.0.0.1:${port}/v1/customers/me`, {
        headers: {
          'x-session-id': signupBody.session.sessionId,
        },
      });
      expect(me.status).toBe(200);
      const meBody = (await me.json()) as {
        customer: { email: string; planId: string; entitlements: { marginDashboard: boolean }; organizationId?: string; organizationRole?: string };
        planName: string;
      };
      expect(meBody.customer.email).toBe('customer@example.com');
      expect(meBody.planName).toBe('Pro');
      expect(meBody.customer.entitlements.marginDashboard).toBe(true);
      expect(meBody.customer.organizationId).toBe(signupBody.customer.organizationId);
      expect(meBody.customer.organizationRole).toBe('owner');

      const list = await fetch(`http://127.0.0.1:${port}/v1/customers`, {
        headers: {
          'x-session-id': signupBody.session.sessionId,
        },
      });
      expect(list.status).toBe(200);
      const listBody = (await list.json()) as { customers: { email: string; planId: string }[] };
      expect(listBody.customers.some((customer) => customer.email === 'customer@example.com')).toBe(true);
    } finally {
      server.close();
    }
  });

  it('produces a treasury plan that separates OpenAI cost, taxes, and owner profit', async () => {
    const ownerId = `treasury-${Date.now().toString(36)}`;
    const session = platform.login(ownerId, 'balanced');
    platform.meter.record({
      ownerId,
      operation: 'capability:invoke',
      units: 120,
      governanceProfile: 'balanced',
      capabilityId: 'cap.demo',
      metadata: { source: 'test' },
    });
    platform.meter.record({
      ownerId,
      operation: 'mesh:route',
      units: 30,
      governanceProfile: 'balanced',
      metadata: { source: 'test' },
    });

    const app = createApp();
    const server = app.listen(0);
    const address = server.address();
    const port = typeof address === 'object' && address ? address.port : 0;

    try {
      const res = await fetch(`http://127.0.0.1:${port}/v1/billing/treasury/plan`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-session-id': session.sessionId,
        },
        body: JSON.stringify({
          customerInvoiceUsd: 500,
          openAiUsageCostUsd: 65,
          taxRatePct: 24,
          profitReservePct: 20,
          platformReservePct: 10,
        }),
      });

      expect(res.status).toBe(201);
      const body = (await res.json()) as {
        plan: {
          grossInvoiceUsd: number;
          openAiUsageCostUsd: number;
          taxReserveUsd: number;
          platformReserveUsd: number;
          ownerProfitUsd: number;
          remittanceInstructions: {
            openAI: { destination: string; channel: string; amountUsd: number };
            tax: { destination: string; channel: string; amountUsd: number; notes: string };
            ownerProfit: { destination: string; channel: string; amountUsd: number };
          };
          adapters: {
            paypalCheckout: { enabled: boolean; apiBaseUrl: string; createOrderPath: string };
            paypalPayout: { enabled: boolean; apiBaseUrl: string; createBatchPath: string };
          };
          usageSnapshot?: { totalUnits: number };
        };
      };

      expect(body.plan.grossInvoiceUsd).toBe(500);
      expect(body.plan.openAiUsageCostUsd).toBe(65);
      expect(body.plan.taxReserveUsd).toBeGreaterThan(0);
      expect(body.plan.platformReserveUsd).toBe(50);
      expect(body.plan.ownerProfitUsd).toBeGreaterThan(0);
      expect(body.plan.remittanceInstructions.openAI.channel).toBe('openai-org-billing');
      expect(body.plan.remittanceInstructions.tax.channel).toBe('irs-direct-pay');
      expect(body.plan.remittanceInstructions.ownerProfit.channel).toBe('paypal-payouts');
      expect(body.plan.remittanceInstructions.tax.notes).toContain('IRS Direct Pay');
      expect(body.plan.adapters.paypalCheckout.apiBaseUrl).toContain('paypal.com');
      expect(body.plan.adapters.paypalCheckout.createOrderPath).toBe('/v2/checkout/orders');
      expect(body.plan.adapters.paypalPayout.apiBaseUrl).toContain('paypal.com');
      expect(body.plan.adapters.paypalPayout.createBatchPath).toBe('/v1/payments/payouts');
      expect(body.plan.usageSnapshot?.totalUnits).toBe(150);
    } finally {
      server.close();
    }
  });

  it('schedules treasury remittances from the ledger with explicit IRS instructions', async () => {
    const ownerId = `schedule-${Date.now().toString(36)}`;
    const session = platform.login(ownerId, 'balanced');
    platform.meter.record({
      ownerId,
      operation: 'billing:evaluate',
      units: 90,
      governanceProfile: 'balanced',
      capabilityId: 'billing.demo',
      metadata: { source: 'test' },
    });

    const app = createApp();
    const server = app.listen(0);
    const address = server.address();
    const port = typeof address === 'object' && address ? address.port : 0;

    try {
      const res = await fetch(`http://127.0.0.1:${port}/v1/billing/treasury/schedule`, {
        headers: {
          'x-session-id': session.sessionId,
        },
      });

      expect(res.status).toBe(200);
      const body = (await res.json()) as {
        schedule: {
          source: 'ledger';
          instructions: {
            openAI: { channel: string; amountUsd: number };
            tax: { channel: string; amountUsd: number; notes: string };
            ownerProfit: { channel: string; amountUsd: number };
          };
          sourcePlan: {
            adapters: {
              paypalCheckout: { apiBaseUrl: string; createOrderPath: string };
              paypalPayout: { apiBaseUrl: string; createBatchPath: string };
            };
            usageSnapshot?: { totalUnits: number };
          };
        };
      };

      expect(body.schedule.source).toBe('ledger');
      expect(body.schedule.instructions.openAI.channel).toBe('openai-org-billing');
      expect(body.schedule.instructions.tax.channel).toBe('irs-direct-pay');
      expect(body.schedule.instructions.ownerProfit.channel).toBe('paypal-payouts');
      expect(body.schedule.instructions.tax.notes).toContain('IRS Direct Pay');
      expect(body.schedule.sourcePlan.adapters.paypalCheckout.apiBaseUrl).toContain('paypal.com');
      expect(body.schedule.sourcePlan.adapters.paypalCheckout.createOrderPath).toBe('/v2/checkout/orders');
      expect(body.schedule.sourcePlan.adapters.paypalPayout.apiBaseUrl).toContain('paypal.com');
      expect(body.schedule.sourcePlan.adapters.paypalPayout.createBatchPath).toBe('/v1/payments/payouts');
      expect(body.schedule.sourcePlan.usageSnapshot?.totalUnits).toBe(90);
    } finally {
      server.close();
    }
  });

  it('evaluates Sovereign Router X pricing through authenticated customer flow and returns a signed Codex reply', async () => {
    const previousSigningSecret = process.env.CODEX_HANDOFF_SIGNING_SECRET;
    process.env.CODEX_HANDOFF_SIGNING_SECRET = 'unit-test-signing-secret';

    const signup = platform.signupCustomer({
      email: `pricing-${Date.now().toString(36)}@example.com`,
      password: 'secret-123',
      displayName: 'Pricing Customer',
      planId: 'pro',
      organizationName: 'Pricing Org',
      organizationRole: 'owner',
      governanceProfile: 'balanced',
    });
    const session = signup.session;
    const app = createApp();
    const server = app.listen(0);
    const address = server.address();
    const port = typeof address === 'object' && address ? address.port : 0;

    try {
      const res = await fetch(`http://127.0.0.1:${port}/v1/billing/pricing/evaluate`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-session-id': session.sessionId,
        },
        body: JSON.stringify({
          customerId: signup.customer.id,
          segment: 'Enterprise',
          monthlyCustomers: 6,
          routedRequestsPerCustomer: 240,
          governanceReviewsPerCustomer: 4,
          knowledgeUpdatesPerCustomer: 6,
          serviceHoursPerCustomer: 3,
          compliancePressure: 70,
          workloadVolatility: 64,
          supportComplexity: 58,
          privateDeployment: true,
          assuranceRequired: true,
          customerInvoiceUsd: 12500,
          openAiUsageCostUsd: 2100,
          taxRatePct: 24,
          profitReservePct: 20,
          platformReservePct: 10,
        }),
      });

      expect(res.status).toBe(201);
      const body = (await res.json()) as {
        evaluation: {
          input: { segment: string };
          recommendedScenario: { strategy: string };
          economics: { monthlyRevenueUsd: number; monthlyDirectCostUsd: number; grossMarginPct: number };
        };
        routeDecisionArtifact: {
          artifactId: string;
          requestId: string;
          trustPacket: { signature?: { value?: string } };
          governance: { result: string };
          signature?: { value?: string };
        };
        treasuryPlan: {
          grossInvoiceUsd: number;
          openAiUsageCostUsd: number;
          taxReserveUsd: number;
          platformReserveUsd: number;
          ownerProfitUsd: number;
        };
        reply: { status: string; summary: string };
        signedReply: { signer: string; signature: string; reply: { summary: string } } | null;
        auditSurface: { signer: string; signature: string; surface: { pricingJustification: string; routingJustification: string; quota: { requestLimit: number; overageBillingUsd: number } } } | null;
        quota: { requestLimit: number; requestCount: number; overageBillingUsd: number };
      };

      expect(body.evaluation.input.segment).toBe('Enterprise');
      expect(body.evaluation.recommendedScenario.strategy).toBeTruthy();
      expect(body.evaluation.economics.monthlyRevenueUsd).toBeGreaterThan(0);
      expect(body.routeDecisionArtifact.artifactId).toBeTruthy();
      expect(body.routeDecisionArtifact.governance.result).toBeDefined();
      expect(body.routeDecisionArtifact.trustPacket.signature?.value).toBeTruthy();
      expect(body.treasuryPlan.grossInvoiceUsd).toBe(12500);
      expect(body.treasuryPlan.openAiUsageCostUsd).toBe(2100);
      expect(body.treasuryPlan.taxReserveUsd).toBeGreaterThan(0);
      expect(body.treasuryPlan.ownerProfitUsd).toBeGreaterThan(0);
      expect(body.reply.status).toBe('done');
      expect(body.reply.summary).toContain('Pricing evaluation completed');
      expect(body.signedReply?.signer).toBe('platform-api');
      expect(body.signedReply?.signature).toMatch(/^[a-f0-9]{64}$/);
      expect(body.auditSurface?.signer).toBe('platform-api');
      expect(body.auditSurface?.signature).toMatch(/^[a-f0-9]{64}$/);
      expect(body.auditSurface?.surface.pricingJustification).toContain('Selected');
      expect(body.auditSurface?.surface.routingJustification).toContain('Routing via');
      expect(body.quota.requestLimit).toBeGreaterThan(0);
      expect(body.quota.requestCount).toBeGreaterThan(0);
    } finally {
      if (previousSigningSecret === undefined) {
        delete process.env.CODEX_HANDOFF_SIGNING_SECRET;
      } else {
        process.env.CODEX_HANDOFF_SIGNING_SECRET = previousSigningSecret;
      }
      server.close();
    }
  });

  it('returns a signed customer audit surface for routing and pricing justification', async () => {
    const previousSigningSecret = process.env.CUSTOMER_AUDIT_SIGNING_SECRET;
    process.env.CUSTOMER_AUDIT_SIGNING_SECRET = 'unit-test-customer-audit-secret';

    const signup = platform.signupCustomer({
      email: 'audit@example.com',
      password: 'secret-123',
      displayName: 'Audit Customer',
      planId: 'pro',
      organizationName: 'Audit Org',
      organizationRole: 'owner',
      governanceProfile: 'balanced',
    });
    platform.meter.record({
      ownerId: signup.session.ownerId,
      operation: 'billing:pricing-evaluate',
      units: 120,
      governanceProfile: 'balanced',
      capabilityId: 'billing.demo',
      metadata: { estimatedTokens: 24_000 },
    });

    const app = createApp();
    const server = app.listen(0);
    const address = server.address();
    const port = typeof address === 'object' && address ? address.port : 0;

    try {
      const res = await fetch(`http://127.0.0.1:${port}/v1/customers/audit-surface`, {
        headers: {
          'x-session-id': signup.session.sessionId,
        },
      });
      expect(res.status).toBe(200);
      const body = (await res.json()) as {
        auditSurface: {
          signer: string;
          signature: string;
          surface: { routingJustification: string; pricingJustification: string; quota: { requestLimit: number; overageBillingUsd: number }; routeDecisionArtifact?: { artifactId?: string } };
        };
      };

      expect(body.auditSurface.signer).toBe('platform-api');
      expect(body.auditSurface.signature).toMatch(/^[a-f0-9]{64}$/);
      expect(body.auditSurface.surface.routingJustification).toContain('Routing tier');
      expect(body.auditSurface.surface.pricingJustification).toContain('Plan');
      expect(body.auditSurface.surface.quota.requestLimit).toBeGreaterThan(0);
    } finally {
      server.close();
      if (previousSigningSecret === undefined) {
        delete process.env.CUSTOMER_AUDIT_SIGNING_SECRET;
      } else {
        process.env.CUSTOMER_AUDIT_SIGNING_SECRET = previousSigningSecret;
      }
    }
  });
});
