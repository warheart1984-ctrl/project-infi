import type { Express, Request, Response } from 'express';

import {
  platform,
  mesh,
  sgce,
  psom,
  sovereignToken,
  parseGovernanceMode,
} from './state.js';
import { asyncHandler, authRequired } from './httpUtils.js';
import {
  buildOAuthStartPayload,
  completeOAuthCallback,
  listOAuthProviders,
} from './oauth.js';
import { createTreasuryPaymentSchedule, createTreasuryPlan, executeTreasuryPayPalCheckout, executeTreasuryPayPalPayout } from './treasury.js';
import { buildPricingEvaluationBundle } from './pricingEvaluation.js';
import { buildRelationshipTrustSurface, signCustomerAuditSurface, type CustomerQuotaSummary } from './customerAudit.js';
import { mountLirlRoutes } from './lirlRoutes.js';
import {
  buildGoogleDriveAuthorization,
  completeGoogleDriveAuthorization,
  createGoogleDriveTextFile,
  fetchGoogleDriveFile,
  getGoogleDriveFile,
  googleDriveStatus,
  listGoogleDriveFiles,
  revokeGoogleDriveToken,
  updateGoogleDriveFile,
  uploadGoogleDriveFile,
} from './googleDrive.js';

function driveOrganization(req: Request): string {
  return req.platformCtx!.organizationId ?? `personal:${req.platformCtx!.ownerId}`;
}

export function mountRoutes(app: Express): void {
  mountLirlRoutes(app);

  app.get('/health', (_req, res) => {
    res.json({ status: 'ok', organismId: process.env.ORGANISM_ID ?? 'organism-local' });
  });

  // v1 auth
  app.post('/v1/auth/login', (req, res) => {
    const ownerId = String(req.body.ownerId ?? 'developer');
    const profile = parseGovernanceMode(req.body.governanceProfile);
    const session = platform.login(ownerId, profile);
    res.json(session);
  });

  app.post('/v1/customers/signup', (req, res) => {
    try {
      const result = platform.signupCustomer({
        email: String(req.body.email ?? ''),
        password: req.body.password ? String(req.body.password) : undefined,
        displayName: req.body.displayName ? String(req.body.displayName) : undefined,
        authProvider: req.body.authProvider,
        authSubject: req.body.authSubject ? String(req.body.authSubject) : undefined,
        planId: req.body.planId,
        organizationId: req.body.organizationId ? String(req.body.organizationId) : undefined,
        organizationName: req.body.organizationName ? String(req.body.organizationName) : undefined,
        organizationRole: req.body.organizationRole,
        governanceProfile: parseGovernanceMode(req.body.governanceProfile),
      });
      res.status(201).json(result);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
    }
  });

  app.post('/v1/customers/login', (req, res) => {
    try {
      const result = platform.loginCustomer({
        email: req.body.email ? String(req.body.email) : undefined,
        password: req.body.password ? String(req.body.password) : undefined,
        authProvider: req.body.authProvider,
        authSubject: req.body.authSubject ? String(req.body.authSubject) : undefined,
        governanceProfile: parseGovernanceMode(req.body.governanceProfile),
      });
      res.json(result);
    } catch (error) {
      res.status(401).json({ error: error instanceof Error ? error.message : String(error) });
    }
  });

  app.get('/v1/auth/oauth/providers', (_req, res) => {
    res.json({ providers: listOAuthProviders() });
  });

  app.get('/v1/auth/oauth/:provider/start', (req, res) => {
    try {
      const provider = String(req.params.provider);
      const mode = req.query.mode === 'login' ? 'login' : 'signup';
      const returnTo = typeof req.query.returnTo === 'string' && req.query.returnTo.trim().length > 0 ? String(req.query.returnTo) : '/pricing';
      res.json(buildOAuthStartPayload(provider as Parameters<typeof buildOAuthStartPayload>[0], mode, returnTo));
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
    }
  });

  app.get('/v1/auth/oauth/:provider/callback', async (req, res) => {
    try {
      const provider = String(req.params.provider);
      const code = String(req.query.code ?? '');
      const state = String(req.query.state ?? '');
      if (!code || !state) {
        res.status(400).json({ error: 'OAUTH: code and state are required' });
        return;
      }
      const result = await completeOAuthCallback({
        provider,
        code,
        state,
        governanceProfile: parseGovernanceMode(req.query.governanceProfile),
      });
      res.json(result);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
    }
  });

  app.get('/v1/integrations/google-drive/start', authRequired, (req, res) => {
    try {
      res.json(buildGoogleDriveAuthorization(req.platformCtx!.ownerId, driveOrganization(req), String(req.query.returnTo ?? '/integrations/google-drive')));
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
    }
  });

  app.get('/v1/integrations/google-drive/callback', asyncHandler(async (req, res) => {
    const code = String(req.query.code ?? '');
    const state = String(req.query.state ?? '');
    if (!code || !state) { res.status(400).json({ error: 'GOOGLE_DRIVE: code and state are required' }); return; }
    res.json(await completeGoogleDriveAuthorization(code, state));
  }));

  app.get('/v1/integrations/google-drive/status', authRequired, asyncHandler(async (req, res) => {
    res.json(await googleDriveStatus(req.platformCtx!.ownerId, driveOrganization(req)));
  }));

  app.delete('/v1/integrations/google-drive', authRequired, asyncHandler(async (req, res) => {
    await revokeGoogleDriveToken(req.platformCtx!.ownerId, driveOrganization(req));
    res.status(204).end();
  }));

  app.get('/v1/integrations/google-drive/files', authRequired, asyncHandler(async (req, res) => {
    res.json(await listGoogleDriveFiles(req.platformCtx!.ownerId, driveOrganization(req), typeof req.query.q === 'string' ? req.query.q : undefined));
  }));

  app.post('/v1/integrations/google-drive/files', authRequired, asyncHandler(async (req, res) => {
    const name = String(req.body.name ?? '').trim();
    if (!name) { res.status(400).json({ error: 'GOOGLE_DRIVE: name is required' }); return; }
    if (req.body.dataBase64) {
      res.status(201).json(await uploadGoogleDriveFile(req.platformCtx!.ownerId, driveOrganization(req), { name, data: Buffer.from(String(req.body.dataBase64), 'base64'), mimeType: String(req.body.mimeType ?? 'application/octet-stream'), parentId: req.body.parentId ? String(req.body.parentId) : undefined }));
    } else {
      res.status(201).json(await createGoogleDriveTextFile(req.platformCtx!.ownerId, driveOrganization(req), { name, content: String(req.body.content ?? ''), mimeType: req.body.mimeType ? String(req.body.mimeType) : undefined, parentId: req.body.parentId ? String(req.body.parentId) : undefined }));
    }
  }));

  app.get('/v1/integrations/google-drive/files/:fileId/content', authRequired, asyncHandler(async (req, res) => {
    res.json(await fetchGoogleDriveFile(req.platformCtx!.ownerId, driveOrganization(req), String(req.params.fileId), typeof req.query.mimeType === 'string' ? req.query.mimeType : undefined));
  }));

  app.patch('/v1/integrations/google-drive/files/:fileId', authRequired, asyncHandler(async (req, res) => {
    if (!req.body.dataBase64) { res.status(400).json({ error: 'GOOGLE_DRIVE: dataBase64 is required' }); return; }
    res.json(await updateGoogleDriveFile(req.platformCtx!.ownerId, driveOrganization(req), String(req.params.fileId), { name: req.body.name ? String(req.body.name) : undefined, mimeType: String(req.body.mimeType ?? 'application/octet-stream'), data: Buffer.from(String(req.body.dataBase64), 'base64') }));
  }));

  app.get('/v1/integrations/google-drive/files/:fileId', authRequired, asyncHandler(async (req, res) => {
    res.json(await getGoogleDriveFile(req.platformCtx!.ownerId, driveOrganization(req), String(req.params.fileId)));
  }));

  app.get('/v1/customers/me', authRequired, (req, res) => {
    if (!req.platformCtx?.customerId) {
      res.status(404).json({ error: 'customer session not found' });
      return;
    }
    const customer = platform.getCustomer(req.platformCtx.customerId);
    if (!customer) {
      res.status(404).json({ error: 'customer not found' });
      return;
    }
    res.json({
      customer,
      entitlements: customer.entitlements,
      planId: customer.planId,
      planName: customer.planName,
      governanceProfile: req.platformCtx.governanceProfile,
      organizationId: customer.organizationId,
      organizationRole: customer.organizationRole,
      organization: customer.organizationId ? platform.getOrganization(customer.organizationId) : undefined,
    });
  });

  app.get('/v1/customers', authRequired, (_req, res) => {
    res.json({
      customers: platform.listCustomers(),
    });
  });

  app.get('/v1/customers/audit-surface', authRequired, (req, res) => {
    if (!req.platformCtx?.customerId) {
      res.status(404).json({ error: 'customer session not found' });
      return;
    }
    const customer = req.platformCtx.customer ?? platform.getCustomer(req.platformCtx.customerId);
    if (!customer) {
      res.status(404).json({ error: 'customer not found' });
      return;
    }
    const usageRecords = platform.meter.allRecords().filter((record) => record.ownerId === req.platformCtx!.ownerId);
    const recentRequests = usageRecords.filter((record) => record.operation === 'billing:pricing-evaluate').length;
    const tokenEstimate = usageRecords.reduce((sum, record) => sum + (typeof record.metadata?.estimatedTokens === 'number' ? record.metadata.estimatedTokens : record.units * 250), 0);
    const quota: CustomerQuotaSummary = {
      requestLimit: customer.entitlements.maxRequestsPerMonth,
      requestCount: recentRequests,
      requestOverage: Math.max(0, recentRequests - customer.entitlements.maxRequestsPerMonth),
      tokenLimit: customer.entitlements.maxTokensPerMonth,
      tokenCount: tokenEstimate,
      tokenOverage: Math.max(0, tokenEstimate - customer.entitlements.maxTokensPerMonth),
      overageBillingUsd: Math.max(0, recentRequests - customer.entitlements.maxRequestsPerMonth) * 0.45,
      overageBillingEnabled: customer.entitlements.overageBillingEnabled,
      enforcement: {
        status:
          recentRequests > customer.entitlements.maxRequestsPerMonth || tokenEstimate > customer.entitlements.maxTokensPerMonth
            ? customer.entitlements.overageBillingEnabled
              ? 'metered_overage'
              : 'blocked'
            : 'within_limit',
        allowed:
          customer.entitlements.overageBillingEnabled ||
          (recentRequests <= customer.entitlements.maxRequestsPerMonth && tokenEstimate <= customer.entitlements.maxTokensPerMonth),
        reason:
          recentRequests > customer.entitlements.maxRequestsPerMonth || tokenEstimate > customer.entitlements.maxTokensPerMonth
            ? customer.entitlements.overageBillingEnabled
              ? 'Overage billed against the entitlement'
              : 'Overage blocked because billing is disabled for this entitlement'
            : 'Within entitlement limits',
      },
    };
    const surface = {
      customerId: customer.id,
      organizationId: customer.organizationId,
      organizationRole: customer.organizationRole,
      planId: customer.planId,
      planName: customer.planName,
      generatedAt: new Date().toISOString(),
      requestId: `audit-${Date.now().toString(36)}`,
      routingJustification: `Routing tier ${customer.entitlements.routingTier} with ${customer.entitlements.allowedModels.join(', ')} model access.`,
      pricingJustification: `Plan ${customer.planName} allows ${customer.entitlements.maxRequestsPerMonth} requests and ${customer.entitlements.maxTokensPerMonth} tokens per month.`,
      entitlements: {
        routingTier: customer.entitlements.routingTier,
        governanceLevel: customer.entitlements.governanceLevel,
        auditScope: customer.entitlements.auditScope,
        customerAuditSurfaces: customer.entitlements.customerAuditSurfaces,
        overageBillingEnabled: customer.entitlements.overageBillingEnabled,
      },
      quota,
      treasury: {
        grossInvoiceUsd: 0,
        openAiUsageCostUsd: 0,
        taxReserveUsd: 0,
        platformReserveUsd: 0,
        ownerProfitUsd: 0,
      },
      pricingPlan: {
        strategy: 'subscription-led',
        packaging: customer.planName,
        targetMarginBand: customer.entitlements.overageBillingEnabled ? '60-90%' : '40-60%',
      },
      trust: buildRelationshipTrustSurface({
        customer,
        requestId: `audit-${Date.now().toString(36)}`,
      }),
    };
    const signed = signCustomerAuditSurface(surface, process.env.CUSTOMER_AUDIT_SIGNING_SECRET ?? 'platform-api-audit', 'platform-api');
    res.json({ auditSurface: signed });
  });

  app.get('/v1/customers/quota', authRequired, (req, res) => {
    if (!req.platformCtx?.customerId) {
      res.status(404).json({ error: 'customer session not found' });
      return;
    }
    const customer = req.platformCtx.customer ?? platform.getCustomer(req.platformCtx.customerId);
    if (!customer) {
      res.status(404).json({ error: 'customer not found' });
      return;
    }
    const usageRecords = platform.meter.allRecords().filter((record) => record.ownerId === req.platformCtx!.ownerId);
    const requestCount = usageRecords.filter((record) => record.operation === 'billing:pricing-evaluate').length;
    const tokenCount = usageRecords.reduce((sum, record) => sum + (typeof record.metadata?.estimatedTokens === 'number' ? record.metadata.estimatedTokens : record.units * 250), 0);
    const requestOverage = Math.max(0, requestCount - customer.entitlements.maxRequestsPerMonth);
    const tokenOverage = Math.max(0, tokenCount - customer.entitlements.maxTokensPerMonth);
    const quota: CustomerQuotaSummary = {
      requestLimit: customer.entitlements.maxRequestsPerMonth,
      requestCount,
      requestOverage,
      tokenLimit: customer.entitlements.maxTokensPerMonth,
      tokenCount,
      tokenOverage,
      overageBillingUsd: Math.max(0, requestOverage * 0.45 + tokenOverage * 0.0000125),
      overageBillingEnabled: customer.entitlements.overageBillingEnabled,
      enforcement: {
        status:
          requestOverage > 0 || tokenOverage > 0
            ? customer.entitlements.overageBillingEnabled
              ? 'metered_overage'
              : 'blocked'
            : 'within_limit',
        allowed:
          customer.entitlements.overageBillingEnabled ||
          (requestOverage === 0 && tokenOverage === 0),
        reason:
          requestOverage > 0 || tokenOverage > 0
            ? customer.entitlements.overageBillingEnabled
              ? 'Overage billed against the entitlement'
              : 'Overage blocked because billing is disabled for this entitlement'
            : 'Within entitlement limits',
      },
    };
    res.json({
      customer,
      usageRecords: usageRecords.slice(-20).reverse(),
      quota,
    });
  });

  app.get('/v1/organizations', authRequired, (_req, res) => {
    res.json({ organizations: platform.listOrganizations() });
  });

  app.get('/v1/organizations/me', authRequired, (req, res) => {
    const organizationId = req.platformCtx?.organizationId;
    if (!organizationId) {
      res.status(404).json({ error: 'organization session not found' });
      return;
    }
    const organization = platform.getOrganization(organizationId);
    if (!organization) {
      res.status(404).json({ error: 'organization not found' });
      return;
    }
    res.json({ organization });
  });

  app.get('/v1/organizations/:organizationId', authRequired, (req, res) => {
    const organization = platform.getOrganization(String(req.params.organizationId));
    if (!organization) {
      res.status(404).json({ error: 'organization not found' });
      return;
    }
    res.json({ organization });
  });

  app.get('/v1/organizations/:organizationId/members', authRequired, (req, res) => {
    const organizationId = String(req.params.organizationId);
    const organization = platform.getOrganization(organizationId);
    if (!organization) {
      res.status(404).json({ error: 'organization not found' });
      return;
    }
    res.json({
      organizationId,
      members: platform.organizations.listMembers(organizationId),
    });
  });

  app.post('/v1/organizations', authRequired, (req, res) => {
    try {
      const organization = platform.createOrganization({
        name: String(req.body.name ?? ''),
        billingContactEmail: String(req.body.billingContactEmail ?? req.platformCtx?.customer?.email ?? ''),
        planId: String(req.body.planId ?? req.platformCtx?.planId ?? req.platformCtx?.customer?.planId ?? 'free'),
        domain: req.body.domain ? String(req.body.domain) : undefined,
        ownerCustomerId: req.platformCtx!.customerId ?? req.platformCtx!.ownerId,
        ownerRole: req.body.ownerRole,
      });
      res.status(201).json({ organization });
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
    }
  });

  app.post('/v1/organizations/:organizationId/members', authRequired, (req, res) => {
    try {
      const organization = platform.addOrganizationMember(String(req.params.organizationId), {
        customerId: String(req.body.customerId ?? ''),
        role: req.body.role,
      });
      res.status(201).json({ organization });
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
    }
  });

  app.patch('/v1/organizations/:organizationId/members/:customerId', authRequired, (req, res) => {
    try {
      const organization = platform.organizations.setMemberRole(
        String(req.params.organizationId),
        String(req.params.customerId),
        req.body.role,
      );
      res.json({ organization });
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
    }
  });

  app.get('/v1/organizations/:organizationId/usage', authRequired, (req, res) => {
    const organizationId = String(req.params.organizationId);
    const organization = platform.getOrganization(organizationId);
    if (!organization) {
      res.status(404).json({ error: 'organization not found' });
      return;
    }
    const summary = platform.getUsageSummary(organizationId);
    res.json({
      organizationId,
      total: summary.total,
      byKind: summary.byKind,
      summary,
      overageEvents: platform.getOverageEvents(organizationId),
    });
  });

  app.post('/v1/organizations/:organizationId/usage', authRequired, (req, res) => {
    try {
      const organizationId = String(req.params.organizationId);
      const organization = platform.getOrganization(organizationId);
      if (!organization) {
        res.status(404).json({ error: 'organization not found' });
        return;
      }
      const event = platform.recordUsage({
        orgId: organizationId,
        customerId: req.platformCtx?.customerId,
        ownerId: req.platformCtx?.ownerId,
        operation: String(req.body.kind ?? 'usage:generic'),
        units: Number(req.body.amount ?? 1),
        governanceProfile: req.platformCtx!.governanceProfile,
        metadata: (req.body.metadata as Record<string, unknown>) ?? undefined,
      });
      res.status(201).json(event);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
    }
  });

  app.get('/v1/organizations/:organizationId/overage', authRequired, (req, res) => {
    const organizationId = String(req.params.organizationId);
    const organization = platform.getOrganization(organizationId);
    if (!organization) {
      res.status(404).json({ error: 'organization not found' });
      return;
    }
    res.json({
      organizationId,
      events: platform.getOverageEvents(organizationId),
    });
  });

  app.post('/v1/organizations/:organizationId/billing/checkout', authRequired, asyncHandler(async (req, res) => {
    const organizationId = String(req.params.organizationId);
    const organization = platform.getOrganization(organizationId);
    if (!organization) {
      res.status(404).json({ error: 'organization not found' });
      return;
    }
    const amount = Number(req.body.amount ?? 0);
    const currency = String(req.body.currency ?? 'USD');
    const session = platform.createCheckoutSession(organizationId, amount, currency);
    const usageRecords = platform.meter.allRecords().filter((record) => record.ownerId === (req.platformCtx!.customerId ?? req.platformCtx!.ownerId));
    const plan = createTreasuryPlan(
      {
        customerId: req.platformCtx!.customerId ?? req.platformCtx!.ownerId,
        ownerId: req.platformCtx!.ownerId,
        governanceProfile: req.platformCtx!.governanceProfile,
        customerInvoiceUsd: amount,
        openAiUsageCostUsd: Math.max(0, amount * 0.08),
        taxRatePct: 22,
        profitReservePct: 18,
        platformReservePct: 8,
      },
      usageRecords,
    );
    const transport = await executeTreasuryPayPalCheckout(
      {
        customerId: plan.customerId,
        ownerId: plan.ownerId,
        governanceProfile: plan.governanceProfile,
        customerInvoiceUsd: plan.grossInvoiceUsd,
        openAiUsageCostUsd: plan.openAiUsageCostUsd,
        taxRatePct: 22,
        profitReservePct: 18,
        platformReservePct: 8,
      },
      amount,
    );
    res.status(201).json({ session, organization, transport, plan });
  }));

  app.post('/v1/organizations/:organizationId/billing/payout', authRequired, asyncHandler(async (req, res) => {
    const organizationId = String(req.params.organizationId);
    const organization = platform.getOrganization(organizationId);
    if (!organization) {
      res.status(404).json({ error: 'organization not found' });
      return;
    }
    const amount = Number(req.body.amount ?? 0);
    const currency = String(req.body.currency ?? 'USD');
    const instruction = platform.createPayoutInstruction(organizationId, amount, currency);
    const usageRecords = platform.meter.allRecords().filter((record) => record.ownerId === (req.platformCtx!.customerId ?? req.platformCtx!.ownerId));
    const plan = createTreasuryPlan(
      {
        customerId: req.platformCtx!.customerId ?? req.platformCtx!.ownerId,
        ownerId: req.platformCtx!.ownerId,
        governanceProfile: req.platformCtx!.governanceProfile,
        customerInvoiceUsd: amount,
        openAiUsageCostUsd: Math.max(0, amount * 0.08),
        taxRatePct: 22,
        profitReservePct: 18,
        platformReservePct: 8,
      },
      usageRecords,
    );
    const transport = await executeTreasuryPayPalPayout(
      {
        customerId: plan.customerId,
        ownerId: plan.ownerId,
        governanceProfile: plan.governanceProfile,
        customerInvoiceUsd: plan.grossInvoiceUsd,
        openAiUsageCostUsd: plan.openAiUsageCostUsd,
        taxRatePct: 22,
        profitReservePct: 18,
        platformReservePct: 8,
      },
      amount,
    );
    res.status(201).json({ instruction, organization, transport, plan });
  }));

  app.get('/v1/organizations/:organizationId/audit/pricing', authRequired, (req, res) => {
    const organizationId = String(req.params.organizationId);
    const organization = platform.getOrganization(organizationId);
    if (!organization) {
      res.status(404).json({ error: 'organization not found' });
      return;
    }
    res.json({ audit: platform.getPricingAudit(organizationId) });
  });

  app.get('/v1/organizations/:organizationId/audit/routing', authRequired, (req, res) => {
    const organizationId = String(req.params.organizationId);
    const organization = platform.getOrganization(organizationId);
    if (!organization) {
      res.status(404).json({ error: 'organization not found' });
      return;
    }
    res.json({ audit: platform.getRoutingAudit(organizationId) });
  });

  app.get('/v1/organizations/:organizationId/audit/entitlements', authRequired, (req, res) => {
    const organizationId = String(req.params.organizationId);
    const organization = platform.getOrganization(organizationId);
    if (!organization) {
      res.status(404).json({ error: 'organization not found' });
      return;
    }
    res.json({ audit: platform.getEntitlementsAudit(organizationId) });
  });

  app.post('/v1/auth/keys', authRequired, (req, res) => {
    const label = String(req.body.label ?? 'api-key');
    const profile = parseGovernanceMode(req.body.governanceProfile ?? req.platformCtx!.governanceProfile);
    const result = platform.apiKeys.create({
      label,
      ownerId: req.platformCtx!.ownerId,
      governanceProfile: profile,
    });
    res.status(201).json({ record: { id: result.record.id, keyPrefix: result.record.keyPrefix }, key: result.key });
  });

  app.get('/v1/auth/keys', authRequired, (req, res) => {
    const keys = platform.apiKeys.list(req.platformCtx!.ownerId).map((k) => ({
      id: k.id,
      label: k.label,
      keyPrefix: k.keyPrefix,
      governanceProfile: k.governanceProfile,
      scopes: k.scopes,
      createdAt: k.createdAt,
    }));
    res.json(keys);
  });

  // v1 governance
  app.get('/v1/governance/profiles', (_req, res) => {
    res.json(platform.listProfiles());
  });

  app.get('/v1/governance/drift', (_req, res) => {
    res.json(psom.drift.scan());
  });

  app.get('/v1/governance/compare', (req, res) => {
    const local = parseGovernanceMode(req.query.local);
    const remote = parseGovernanceMode(req.query.remote ?? 'experimental');
    res.json(psom.governance.negotiate(local, remote));
  });

  // v1 capabilities
  app.get('/v1/capabilities', authRequired, (_req, res) => {
    res.json(platform.versions.list());
  });

  app.post('/v1/capabilities/publish', authRequired, (req, res) => {
    const record = platform.publishCapability(req.platformCtx!, {
      id: String(req.body.id),
      name: String(req.body.name),
      description: String(req.body.description ?? ''),
      organId: String(req.body.organId),
      version: String(req.body.version),
      changelog: req.body.changelog as string | undefined,
    });
    sgce.provenance.record({
      capabilityId: record.id,
      version: record.currentVersion,
      publisherId: req.platformCtx!.ownerId,
      governanceTags: (req.body.governanceTags as string[]) ?? [],
    });
    res.status(201).json(record);
  });

  app.post('/v1/capabilities/:capabilityId/invoke', authRequired, (req, res) => {
    const result = platform.invokeCapability(req.platformCtx!, {
      capabilityId: String(req.params.capabilityId),
      version: req.body.version as string | undefined,
      input: (req.body.input as Record<string, unknown>) ?? {},
      traceId: req.body._governance?.traceId as string | undefined,
    });
    res.json(result);
  });

  // v1 billing
  app.get('/v1/billing/usage', authRequired, (req, res) => {
    res.json(platform.meter.summary(req.platformCtx!.ownerId));
  });

  app.post('/v1/billing/pricing/evaluate', authRequired, (req, res) => {
    const ownerId = req.platformCtx!.customerId ?? req.platformCtx!.ownerId;
    const sessionProfile = req.platformCtx!.governanceProfile;
    const customer = req.platformCtx!.customer ?? (req.platformCtx!.customerId ? platform.getCustomer(req.platformCtx!.customerId) : undefined);
    if (!customer) {
      res.status(404).json({ error: 'customer not found' });
      return;
    }
    const usageRecords = platform.meter.allRecords().filter((record) => record.ownerId === ownerId);
    const bundle = buildPricingEvaluationBundle({
      ownerId,
      customerId: String(req.body.customerId ?? ownerId),
      customer,
      customerEntitlements: customer.entitlements,
      governanceProfile: sessionProfile,
      trustSurface: (req.body.trustSurface as Parameters<typeof buildPricingEvaluationBundle>[0]['trustSurface']) ?? undefined,
      usageRecords,
      pricing: {
        segment: req.body.segment ?? 'Professional',
        monthlyCustomers: Number(req.body.monthlyCustomers ?? 1),
        routedRequestsPerCustomer: Number(req.body.routedRequestsPerCustomer ?? 120),
        governanceReviewsPerCustomer: Number(req.body.governanceReviewsPerCustomer ?? 2),
        knowledgeUpdatesPerCustomer: Number(req.body.knowledgeUpdatesPerCustomer ?? 4),
        serviceHoursPerCustomer: Number(req.body.serviceHoursPerCustomer ?? 0),
        compliancePressure: Number(req.body.compliancePressure ?? 35),
        workloadVolatility: Number(req.body.workloadVolatility ?? 45),
        supportComplexity: Number(req.body.supportComplexity ?? 35),
        privateDeployment: Boolean(req.body.privateDeployment ?? false),
        assuranceRequired: Boolean(req.body.assuranceRequired ?? false),
        customerInvoiceUsd: Number(req.body.customerInvoiceUsd ?? undefined),
      },
      openAiUsageCostUsd: Number(req.body.openAiUsageCostUsd ?? undefined),
      taxRatePct: Number(req.body.taxRatePct ?? 22),
      profitReservePct: Number(req.body.profitReservePct ?? 18),
      platformReservePct: Number(req.body.platformReservePct ?? 8),
      signingSecret: process.env.CODEX_HANDOFF_SIGNING_SECRET,
    });

    if (!customer.entitlements.overageBillingEnabled && (bundle.quota.requestOverage > 0 || bundle.quota.tokenOverage > 0)) {
      platform.recordOverage({
        orgId: customer.organizationId ?? req.platformCtx!.ownerId,
        kind: 'billing:pricing-evaluate',
        amount: bundle.quota.overageBillingUsd,
        metadata: {
          requestOverage: bundle.quota.requestOverage,
          tokenOverage: bundle.quota.tokenOverage,
          requestId: bundle.auditSurface.requestId,
        },
      });
      res.status(429).json({
        error: 'quota exceeded',
        quota: bundle.quota,
      });
      return;
    }

    if (bundle.quota.requestOverage > 0 || bundle.quota.tokenOverage > 0) {
      platform.recordOverage({
        orgId: customer.organizationId ?? req.platformCtx!.ownerId,
        kind: 'billing:pricing-evaluate',
        amount: bundle.quota.overageBillingUsd,
        metadata: {
          requestOverage: bundle.quota.requestOverage,
          tokenOverage: bundle.quota.tokenOverage,
          requestId: bundle.auditSurface.requestId,
        },
      });
    }

    platform.meter.record(bundle.usageRecord);

    res.status(201).json({
      evaluation: bundle.evaluation,
      routeDecisionArtifact: bundle.routeDecisionArtifact,
      treasuryPlan: bundle.treasuryPlan,
      reply: bundle.reply,
      signedReply: bundle.signedReply,
      auditSurface: bundle.signedAuditSurface,
      quota: bundle.quota,
    });
  });

  app.post('/v1/billing/treasury/plan', authRequired, (req, res) => {
    const ownerId = req.platformCtx!.customerId ?? req.platformCtx!.ownerId;
    const usageRecords = platform.meter.allRecords().filter((record) => record.ownerId === ownerId);
    const plan = createTreasuryPlan(
      {
        customerId: String(req.body.customerId ?? ownerId),
        ownerId,
        governanceProfile: req.platformCtx!.governanceProfile,
        customerInvoiceUsd: Number(req.body.customerInvoiceUsd ?? Math.max(49, platform.meter.summary(ownerId).totalUnits * 0.08 + 49)),
        openAiUsageCostUsd: Number(req.body.openAiUsageCostUsd ?? Math.max(0, platform.meter.summary(ownerId).totalUnits * 0.012)),
        taxRatePct: Number(req.body.taxRatePct ?? 22),
        profitReservePct: Number(req.body.profitReservePct ?? 18),
        platformReservePct: Number(req.body.platformReservePct ?? 8),
      },
      usageRecords,
    );
    res.status(201).json({ plan });
  });

  app.get('/v1/billing/treasury/plan', authRequired, (req, res) => {
    const ownerId = req.platformCtx!.customerId ?? req.platformCtx!.ownerId;
    const usageRecords = platform.meter.allRecords().filter((record) => record.ownerId === ownerId);
    const summary = platform.meter.summary(ownerId);
    const plan = createTreasuryPlan(
      {
        customerId: ownerId,
        ownerId,
        governanceProfile: req.platformCtx!.governanceProfile,
        customerInvoiceUsd: Math.max(49, summary.totalUnits * 0.08 + 49),
        openAiUsageCostUsd: Math.max(0, summary.totalUnits * 0.012),
        taxRatePct: 22,
        profitReservePct: 18,
        platformReservePct: 8,
      },
      usageRecords,
    );
    res.json({ plan });
  });

  app.get('/v1/billing/treasury/schedule', authRequired, (req, res) => {
    const ownerId = req.platformCtx!.ownerId;
    const usageRecords = platform.meter.allRecords().filter((record) => record.ownerId === ownerId);
    const schedule = createTreasuryPaymentSchedule(
      {
        customerId: ownerId,
        ownerId,
        governanceProfile: req.platformCtx!.governanceProfile,
        customerInvoiceUsd: Math.max(49, platform.meter.summary(ownerId).totalUnits * 0.08 + 49),
        openAiUsageCostUsd: Math.max(0, platform.meter.summary(ownerId).totalUnits * 0.012),
        taxRatePct: 22,
        profitReservePct: 18,
        platformReservePct: 8,
      },
      usageRecords,
    );
    res.json({ schedule });
  });

  // v1 modules
  app.post('/v1/modules/test', authRequired, (req, res) => {
    const result = platform.testModule(
      req.platformCtx!,
      String(req.body.moduleId),
      String(req.body.version),
    );
    res.json(result);
  });

  // v1 mesh
  app.get('/v1/mesh/discover', (req, res) => {
    const capability = req.query.capability as string | undefined;
    const governanceProfile = req.query.governanceProfile
      ? parseGovernanceMode(req.query.governanceProfile)
      : undefined;
    res.json(mesh.discover({ capability, governanceProfile }));
  });

  app.get('/v1/mesh/topology', (_req, res) => {
    res.json(psom.topology());
  });

  app.post('/v1/mesh/connect', authRequired, (req, res) => {
    const organismId = String(req.body.organismId ?? req.body.nodeId);
    const remote = mesh.discover().find((o) => o.organismId === organismId);
    if (!remote) {
      res.status(404).json({ error: `organism "${organismId}" not discovered` });
      return;
    }
    const token = sovereignToken(req.platformCtx!.ownerId);
    const conn = mesh.connect(
      remote,
      (req.body.scope as string[]) ?? ['capabilities:read', 'capabilities:invoke'],
      token,
      req.platformCtx!.governanceProfile,
    );
    res.status(201).json(conn);
  });

  app.post('/v1/mesh/announce', authRequired, (req, res) => {
    const descriptor = mesh.announce({
      organismId: String(req.body.organismId),
      endpoint: String(req.body.endpoint),
      capabilities: (req.body.capabilities as string[]) ?? [],
      governanceProfile: parseGovernanceMode(req.body.governanceProfile),
      lawHash: String(req.body.lawHash ?? process.env.PLATFORM_LAW_HASH ?? 'platform-law-v1'),
    });
    psom.registry.register({
      nodeId: descriptor.organismId,
      organismId: descriptor.organismId,
      endpoint: descriptor.endpoint,
      governanceProfile: descriptor.governanceProfile,
      capabilities: descriptor.capabilities,
    });
    res.status(201).json(descriptor);
  });

  // v1 workflows
  app.post('/v1/workflows/run', authRequired, (req, res) => {
    const token = sovereignToken(req.platformCtx!.ownerId);
    const result = mesh.routeWorkflow(
      {
        workflowId: `wf_${Date.now().toString(36)}`,
        steps: req.body.steps,
        governanceProfile: req.platformCtx!.governanceProfile,
      },
      token,
    );
    res.json(result);
  });

  // v1 marketplace (SGCE)
  app.get('/v1/marketplace', (req, res) => {
    const profile = req.query.profile ? parseGovernanceMode(req.query.profile) : undefined;
    res.json(sgce.marketplace.search({ governanceProfile: profile }));
  });

  app.post('/v1/marketplace/list', authRequired, (req, res) => {
    const listing = sgce.marketplace.publish({
      capabilityId: String(req.body.capabilityId),
      version: String(req.body.version),
      sellerId: req.platformCtx!.ownerId,
      title: String(req.body.title),
      description: String(req.body.description ?? ''),
      pricingModel: req.body.pricingModel ?? 'subscription',
      priceUnits: Number(req.body.priceUnits ?? 10),
      governanceProfile: parseGovernanceMode(req.body.governanceProfile ?? req.platformCtx!.governanceProfile),
    });
    res.status(201).json(listing);
  });

  // Legacy unversioned aliases
  app.get('/governance/profiles', (_req, res) => res.redirect(307, '/v1/governance/profiles'));
  app.get('/mesh/topology', (_req, res) => res.redirect(307, '/v1/mesh/topology'));
}

export { asyncHandler, authRequired } from './httpUtils.js';
