import { describe, expect, it } from 'vitest';

import { PlatformService } from './PlatformService.js';

describe('PlatformService', () => {
  it('login, publish, invoke with billing', () => {
    const platform = new PlatformService();
    const session = platform.login('dev-1', 'balanced');
    expect(session.ownerId).toBe('dev-1');

    const ctx = { ownerId: 'dev-1', governanceProfile: 'balanced' as const, scopes: ['*'] };
    platform.publishCapability(ctx, {
      id: 'cap.demo',
      name: 'Demo',
      description: 'test',
      organId: 'organ-1',
      version: '1.0.0',
    });

    const result = platform.invokeCapability(ctx, {
      capabilityId: 'cap.demo',
      input: { hello: 'world' },
    });

    expect(result.governance.allowed).toBe(true);
    expect(result.billing.units).toBeGreaterThan(0);

    const usage = platform.meter.summary('dev-1');
    expect(usage.totalUnits).toBeGreaterThan(0);
  });

  it('creates customer accounts with plan entitlements and signed sessions', () => {
    const platform = new PlatformService();
    const signup = platform.signupCustomer({
      email: 'customer@example.com',
      password: 'secret-123',
      displayName: 'Customer One',
      planId: 'pro',
      organizationName: 'Customer Org',
      organizationRole: 'owner',
      governanceProfile: 'balanced',
    });

    expect(signup.customer.email).toBe('customer@example.com');
    expect(signup.customer.planId).toBe('pro');
    expect(signup.customer.entitlements.codexPacketHandoff).toBe(true);
    expect(signup.customer.organizationId).toBeTruthy();
    expect(signup.customer.organizationRole).toBe('owner');
    expect(signup.session.customerId).toBe(signup.customer.id);

    const login = platform.loginCustomer({
      email: 'customer@example.com',
      password: 'secret-123',
      governanceProfile: 'strict',
    });

    expect(login.customer.email).toBe('customer@example.com');
    expect(login.session.planName).toBe('Pro');
    expect(login.session.entitlements.marginDashboard).toBe(true);
    expect(login.session.organizationId).toBe(signup.customer.organizationId);
    expect(platform.getCustomerSession(login.session.sessionId)?.customerId).toBe(login.customer.id);
    expect(platform.listCustomers()).toHaveLength(1);
    expect(platform.listOrganizations()).toHaveLength(1);
  });

  it('tracks org scoped usage, quota, checkout, payout, and audit packets', () => {
    const platform = new PlatformService();
    const signup = platform.signupCustomer({
      email: 'org-owner@example.com',
      password: 'secret-123',
      displayName: 'Org Owner',
      planId: 'enterprise',
      organizationName: 'Org Plus',
      organizationRole: 'owner',
      governanceProfile: 'balanced',
    });

    const organizationId = signup.customer.organizationId;
    expect(organizationId).toBeTruthy();
    if (!organizationId) {
      return;
    }
    const organization = platform.getOrganization(organizationId);
    expect(organization?.planId).toBe('enterprise');
    expect(platform.listCustomerOrgs(signup.customer.id)).toHaveLength(1);

    const usage = platform.recordUsage({
      orgId: organizationId,
      customerId: signup.customer.id,
      ownerId: signup.customer.id,
      operation: 'billing:pricing-evaluate',
      units: 140,
      governanceProfile: 'balanced',
      metadata: { estimatedTokens: 34_000 },
    });

    expect(usage.orgId).toBe(organizationId);

    const quota = platform.evaluateQuota(signup.customer.id, organizationId);
    expect(quota.requestLimit).toBeGreaterThan(0);
    expect(quota.enforcement.status).toBe('within_limit');

    const usageSummary = platform.getUsageSummary(organizationId);
    expect(usageSummary.total).toBeGreaterThan(0);

    const checkout = platform.createCheckoutSession(organizationId, 199, 'USD');
    const payout = platform.createPayoutInstruction(organizationId, 75, 'USD');
    expect(checkout.provider).toBe('paypal');
    expect(payout.provider).toBe('paypal');

    const pricingAudit = platform.getPricingAudit(organizationId);
    const routingAudit = platform.getRoutingAudit(organizationId);
    const entitlementsAudit = platform.getEntitlementsAudit(organizationId);

    expect(pricingAudit[0].orgId).toBe(organizationId);
    expect(routingAudit[0].orgId).toBe(organizationId);
    expect(entitlementsAudit[0].orgId).toBe(organizationId);

    const updated = platform.updateOrgMemberRole(organizationId, signup.customer.id, 'admin');
    expect(updated.members.find((member) => member.customerId === signup.customer.id)?.role).toBe('admin');

    const overage = platform.recordOverage({
      orgId: organizationId,
      kind: 'billing:pricing-evaluate',
      amount: 12.5,
      metadata: { reason: 'test' },
    });
    expect(platform.getOverageEvents(organizationId)[0].id).toBe(overage.id);
  });
});
