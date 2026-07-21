import type { CognitiveRisk } from '@aaes-os/governed-runtime';

import { ApiKeyStore } from './auth/apiKeys.js';
import type { CustomerLoginInput, CustomerSignupInput } from './auth/customers.js';
import { CustomerStore } from './auth/customers.js';
import { UsageMeter } from './billing/meter.js';
import {
  assertApiAccess,
  assertBehaviorAllowed,
  getGovernanceProfile,
  listGovernanceProfiles,
} from './governance/profiles.js';
import type {
  CapabilityRecord,
  CustomerRecord,
  CustomerSession,
  GovernanceMode,
  InvokeRequest,
  InvokeResult,
  OverageEvent,
  OrganizationRecord,
  OrganizationRole,
  OrgMember,
  UsageRecord,
} from './types.js';
import type { EntitlementsAuditPacket, PricingAuditPacket, RoutingAuditPacket } from './audit/audit.js';
import type { CheckoutSession, PayoutInstruction, TreasuryStore } from './treasury/treasury.js';
import type { QuotaEnforcementResult } from './usage/usage.js';
import { VersionRegistry } from './versioning/registry.js';

export interface PlatformContext {
  ownerId: string;
  customerId?: string;
  planId?: string;
  customer?: CustomerRecord;
  entitlements?: CustomerRecord['entitlements'];
  organizationId?: string;
  organizationRole?: OrganizationRole;
  organization?: OrganizationRecord;
  governanceProfile: GovernanceMode;
  scopes: string[];
}

export class PlatformService {
  readonly apiKeys = new ApiKeyStore();
  readonly customers = new CustomerStore();
  readonly organizations = this.customers.organizations;
  readonly versions = new VersionRegistry();
  readonly meter = new UsageMeter();
  readonly treasury: TreasuryStore = {
    async getOrgBalance() {
      return { balance: 0, currency: 'USD' };
    },
    async recordCharge() {
      return undefined;
    },
    async recordPayout() {
      return undefined;
    },
  };

  authenticateApiKey(key: string): PlatformContext {
    const record = this.apiKeys.authenticate(key);
    return {
      ownerId: record.ownerId,
      governanceProfile: record.governanceProfile,
      scopes: record.scopes,
    };
  }

  login(ownerId: string, governanceProfile: GovernanceMode = 'balanced') {
    return this.apiKeys.login(ownerId, governanceProfile);
  }

  signupCustomer(input: CustomerSignupInput): { customer: CustomerRecord; session: CustomerSession } {
    return this.customers.signup(input);
  }

  loginCustomer(input: CustomerLoginInput): { customer: CustomerRecord; session: CustomerSession } {
    return this.customers.login(input);
  }

  listOrganizations(): OrganizationRecord[] {
    return this.organizations.list();
  }

  getOrganization(organizationId: string): OrganizationRecord | undefined {
    return this.organizations.get(organizationId);
  }

  createOrganization(input: {
    name: string;
    billingContactEmail: string;
    planId: string;
    domain?: string;
    ownerCustomerId: string;
    ownerRole?: OrganizationRole;
  }): OrganizationRecord {
    return this.organizations.create(input);
  }

  createOrgForCustomer(customerId: string, name: string, planId: string): OrganizationRecord {
    const customer = this.getCustomer(customerId);
    if (!customer) {
      throw new Error('PLATFORM: customer not found');
    }
    return this.createOrganization({
      name,
      billingContactEmail: customer.email,
      planId,
      ownerCustomerId: customerId,
      ownerRole: 'owner',
      domain: planId ? `${planId}.local` : undefined,
    });
  }

  listCustomerOrgs(customerId: string): OrganizationRecord[] {
    return this.organizations.list().filter((organization) =>
      organization.ownerCustomerId === customerId ||
      organization.members.some((member) => member.customerId === customerId),
    );
  }

  getOrgMember(organizationId: string, customerId: string): OrgMember | undefined {
    const member = this.organizations.listMembers(organizationId).find((entry) => entry.customerId === customerId);
    return member ? { orgId: organizationId, customerId: member.customerId, role: member.role, createdAt: member.joinedAt } : undefined;
  }

  listOrgMembers(organizationId: string): OrgMember[] {
    return this.organizations.listMembers(organizationId).map((member) => ({
      orgId: organizationId,
      customerId: member.customerId,
      role: member.role,
      createdAt: member.joinedAt,
    }));
  }

  addOrganizationMember(
    organizationId: string,
    input: { customerId: string; role: OrganizationRole },
  ): OrganizationRecord {
    return this.organizations.addMember(organizationId, input);
  }

  updateOrgMemberRole(
    organizationId: string,
    customerId: string,
    role: OrganizationRole,
  ): OrganizationRecord {
    return this.organizations.setMemberRole(organizationId, customerId, role);
  }

  getCustomer(customerId: string): CustomerRecord | undefined {
    return this.customers.get(customerId);
  }

  listCustomers(): CustomerRecord[] {
    return this.customers.list();
  }

  getCustomerSession(sessionId: string): CustomerSession | undefined {
    return this.customers.getSession(sessionId);
  }

  recordUsage(input: {
    orgId: string;
    customerId?: string;
    ownerId?: string;
    operation: string;
    units: number;
    governanceProfile?: GovernanceMode;
    capabilityId?: string;
    metadata?: Record<string, unknown>;
  }): UsageRecord {
    return this.meter.record({
      ownerId: input.ownerId ?? input.orgId,
      orgId: input.orgId,
      customerId: input.customerId,
      capabilityId: input.capabilityId,
      operation: input.operation,
      units: input.units,
      governanceProfile: input.governanceProfile ?? 'balanced',
      metadata: input.metadata,
    });
  }

  recordOverage(input: {
    orgId: string;
    kind: string;
    amount: number;
    metadata?: Record<string, unknown>;
  }): OverageEvent {
    return this.meter.recordOverage({
      orgId: input.orgId,
      kind: input.kind,
      amount: input.amount,
      metadata: input.metadata,
    });
  }

  getUsageSummary(orgId: string): { total: number; byKind: Record<string, number> } {
    return this.meter.usageSummary(orgId);
  }

  getOverageEvents(orgId: string): OverageEvent[] {
    return this.meter.listOverages(orgId);
  }

  evaluateQuota(customerId: string, ownerId?: string): QuotaEnforcementResult {
    const customer = this.getCustomer(customerId);
    if (!customer) {
      throw new Error('PLATFORM: customer not found');
    }
    const scopeId = ownerId ?? customer.organizationId ?? customer.ownerId;
    const usageRecords = this.meter.allRecords().filter((record) => record.ownerId === scopeId || record.orgId === customer.organizationId);
    const requestCount = usageRecords.filter((record) => record.operation === 'billing:pricing-evaluate').length;
    const tokenCount = usageRecords.reduce(
      (sum, record) => sum + (typeof record.metadata?.estimatedTokens === 'number' ? record.metadata.estimatedTokens : record.units * 250),
      0,
    );
    const requestOverage = Math.max(0, requestCount - customer.entitlements.maxRequestsPerMonth);
    const tokenOverage = Math.max(0, tokenCount - customer.entitlements.maxTokensPerMonth);
    const overageBillingUsd = Math.max(0, requestOverage * 0.45 + tokenOverage * 0.0000125);
    const hasOverage = requestOverage > 0 || tokenOverage > 0;
    const allowed = customer.entitlements.overageBillingEnabled || !hasOverage;

    return {
      requestLimit: customer.entitlements.maxRequestsPerMonth,
      requestCount,
      requestOverage,
      tokenLimit: customer.entitlements.maxTokensPerMonth,
      tokenCount,
      tokenOverage,
      overageBillingUsd,
      overageBillingEnabled: customer.entitlements.overageBillingEnabled,
      enforcement: {
        status: hasOverage ? (customer.entitlements.overageBillingEnabled ? 'metered_overage' : 'blocked') : 'within_limit',
        allowed,
        reason: hasOverage
          ? customer.entitlements.overageBillingEnabled
            ? 'Overage billed against the entitlement'
            : 'Overage blocked because billing is disabled for this entitlement'
          : 'Within entitlement limits',
      },
    };
  }

  createCheckoutSession(orgId: string, amount: number, currency: string): CheckoutSession {
    return {
      id: `checkout_${Date.now().toString(36)}`,
      orgId,
      amount,
      currency,
      provider: 'paypal',
      url: `${process.env.PAYPAL_RETURN_URL ?? 'https://www.paypal.com'}/checkout/${orgId}/${amount.toFixed(2)}`,
    };
  }

  createPayoutInstruction(orgId: string, amount: number, currency: string): PayoutInstruction {
    return {
      id: `payout_${Date.now().toString(36)}`,
      orgId,
      amount,
      currency,
      provider: 'paypal',
    };
  }

  getPricingAudit(orgId: string): PricingAuditPacket[] {
    const usage = this.getUsageSummary(orgId);
    return [{
      id: `pricing_${orgId}`,
      orgId,
      requestId: `req_${orgId}`,
      modelId: 'sovereign-router-x',
      price: usage.total * 0.08,
      currency: 'USD',
      breakdown: usage,
      createdAt: new Date().toISOString(),
    }];
  }

  getRoutingAudit(orgId: string): RoutingAuditPacket[] {
    const org = this.getOrganization(orgId);
    const pricingEvaluations = this.meter
      .allRecords()
      .filter((record) => (record.orgId ?? record.ownerId) === orgId && record.operation === 'billing:pricing-evaluate')
      .sort((left, right) => right.timestamp.localeCompare(left.timestamp));
    const latestEvaluation = pricingEvaluations[0];
    const routeDecisionArtifact = latestEvaluation?.metadata?.routeDecisionArtifact;

    if (routeDecisionArtifact && typeof routeDecisionArtifact === 'object') {
      const artifact = routeDecisionArtifact as {
        artifactId?: string;
        requestId?: string;
        orgId?: string;
        customerId?: string;
        createdAt?: string;
        trustPacket?: unknown;
        routeEvaluation?: unknown;
        governance?: unknown;
        replay?: unknown;
        provenance?: unknown;
        signature?: unknown;
      };

      return [{
        id: artifact.artifactId ?? `routing_${orgId}`,
        orgId,
        requestId: artifact.requestId ?? latestEvaluation?.id ?? `req_${orgId}`,
        modelId: typeof artifact.routeEvaluation === 'object' && artifact.routeEvaluation && 'effectiveDecision' in artifact.routeEvaluation
          ? String((artifact.routeEvaluation as { effectiveDecision?: { model?: string } }).effectiveDecision?.model ?? 'sovereign-router-x')
          : 'sovereign-router-x',
        justification: {
          organization: org?.name ?? orgId,
          members: this.listOrgMembers(orgId),
          latestUsageRecordId: latestEvaluation?.id ?? null,
          trustPacket: artifact.trustPacket ?? null,
          routeEvaluation: artifact.routeEvaluation ?? null,
          governance: artifact.governance ?? null,
          replay: artifact.replay ?? null,
          provenance: artifact.provenance ?? null,
          signature: artifact.signature ?? null,
          routeDecisionArtifact: artifact,
        },
        createdAt: typeof artifact.createdAt === 'string' ? artifact.createdAt : new Date().toISOString(),
      }];
    }

    return [{
      id: `routing_${orgId}`,
      orgId,
      requestId: `req_${orgId}`,
      modelId: 'sovereign-router-x',
      justification: {
        organization: org?.name ?? orgId,
        members: this.listOrgMembers(orgId),
      },
      createdAt: new Date().toISOString(),
    }];
  }

  getEntitlementsAudit(orgId: string): EntitlementsAuditPacket[] {
    const org = this.getOrganization(orgId);
    const members = org ? this.listOrgMembers(org.id) : [];
    return members.map((member) => ({
      id: `entitlements_${orgId}_${member.customerId}`,
      orgId,
      customerId: member.customerId,
      entitlements: this.getCustomer(member.customerId)?.entitlements ?? null,
      createdAt: new Date().toISOString(),
    }));
  }

  listProfiles() {
    return listGovernanceProfiles();
  }

  publishCapability(
    ctx: PlatformContext,
    input: {
      id: string;
      name: string;
      description: string;
      organId: string;
      version: string;
      changelog?: string;
      maxRisk?: CognitiveRisk;
      requiredInvariants?: string[];
    },
  ): CapabilityRecord {
    assertBehaviorAllowed(getGovernanceProfile(ctx.governanceProfile), 'publish-capability');
    assertApiAccess(getGovernanceProfile(ctx.governanceProfile), 'standard');

    const profile = getGovernanceProfile(ctx.governanceProfile);
    return this.versions.publish({
      id: input.id,
      name: input.name,
      description: input.description,
      organId: input.organId,
      ownerId: ctx.ownerId,
      governanceProfile: ctx.governanceProfile,
      version: input.version,
      changelog: input.changelog,
      compatibility: {
        minPlatform: '0.1.0',
        maxRisk: input.maxRisk ?? profile.riskThreshold,
        requiredInvariants: input.requiredInvariants ?? profile.invariantSets,
      },
    });
  }

  invokeCapability(ctx: PlatformContext, req: InvokeRequest): InvokeResult {
    const cap = this.versions.get(req.capabilityId);
    if (!cap) {
      throw new Error(`PLATFORM: capability "${req.capabilityId}" not found`);
    }

    const version = req.version ?? cap.currentVersion;
    const versionEntry = this.versions.getVersion(req.capabilityId, version);
    if (!versionEntry) {
      throw new Error(`PLATFORM: version "${version}" not found for ${req.capabilityId}`);
    }

    const profile = getGovernanceProfile(ctx.governanceProfile);
    const check = this.versions.checkCompatibility(
      req.capabilityId,
      cap.currentVersion,
      version,
      ctx.governanceProfile,
      profile.riskThreshold,
    );

    const violations = [...check.reasons];
    if (!check.compatible) {
      if (ctx.governanceProfile === 'strict') {
        throw new Error(`PLATFORM: invoke blocked — ${violations.join('; ')}`);
      }
    }

    const units = this.meter.computeUnits('capability:invoke', 1, ctx.governanceProfile);
    this.meter.record({
      ownerId: ctx.ownerId,
      orgId: ctx.organizationId,
      customerId: ctx.customerId,
      capabilityId: req.capabilityId,
      operation: 'capability:invoke',
      units,
      governanceProfile: ctx.governanceProfile,
      metadata: { version, traceId: req.traceId },
    });

    return {
      capabilityId: req.capabilityId,
      version,
      output: {
        status: 'ok',
        echo: req.input,
        executedAt: new Date().toISOString(),
      },
      governance: {
        profile: ctx.governanceProfile,
        violations,
        allowed: check.compatible,
      },
      billing: {
        units,
        operation: 'capability:invoke',
      },
    };
  }

  testModule(
    ctx: PlatformContext,
    moduleId: string,
    version: string,
  ): { passed: boolean; checks: string[] } {
    assertApiAccess(getGovernanceProfile(ctx.governanceProfile), 'standard');
    const cap = this.versions.get(moduleId);
    const checks: string[] = [];

    if (!cap) {
      return { passed: false, checks: [`module "${moduleId}" not registered`] };
    }

    const v = this.versions.getVersion(moduleId, version);
    if (!v) {
      checks.push(`version ${version} not found`);
    } else {
      checks.push(`version ${version} resolved`);
      checks.push(`organ ${v.organId} linked`);
    }

    const compat = this.versions.checkCompatibility(
      moduleId,
      cap.currentVersion,
      version,
      ctx.governanceProfile,
    );
    checks.push(...compat.reasons.map((r: string) => `compat: ${r}`));
    if (compat.compatible) checks.push('compatibility check passed');

    const units = this.meter.computeUnits('module:test', 1, ctx.governanceProfile);
    this.meter.record({
      ownerId: ctx.ownerId,
      orgId: ctx.organizationId,
      customerId: ctx.customerId,
      capabilityId: moduleId,
      operation: 'module:test',
      units,
      governanceProfile: ctx.governanceProfile,
    });

    return { passed: compat.compatible && !!v, checks };
  }
}
