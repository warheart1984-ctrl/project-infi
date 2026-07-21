import { createHash, randomBytes, scryptSync, timingSafeEqual } from 'node:crypto';

import type {
  CustomerAuthProvider,
  CustomerEntitlements,
  CustomerPlanId,
  CustomerRecord,
  CustomerSession,
  GovernanceMode,
  OrganizationRole,
} from '../types.js';
import { OrganizationStore } from './organizations.js';

export interface CustomerSignupInput {
  email: string;
  password?: string;
  displayName?: string;
  authProvider?: CustomerAuthProvider;
  authSubject?: string;
  planId?: CustomerPlanId;
  organizationId?: string;
  organizationName?: string;
  organizationRole?: OrganizationRole;
  governanceProfile?: GovernanceMode;
}

export interface CustomerLoginInput {
  email?: string;
  password?: string;
  authProvider?: CustomerAuthProvider;
  authSubject?: string;
  governanceProfile?: GovernanceMode;
}

interface StoredCustomer extends CustomerRecord {
  passwordSalt?: string;
  passwordHash?: string;
}

const PLAN_PRESETS: Record<CustomerPlanId, { planName: string; entitlements: CustomerEntitlements }> = {
  free: {
    planName: 'Free',
    entitlements: {
      maxRequestsPerMonth: 250,
      maxTokensPerMonth: 75_000,
      allowedModels: ['qwen-3b'],
      routingTier: 'basic',
      codexPacketHandoff: false,
      usageLedger: true,
      marginDashboard: false,
      treasuryAccess: false,
      governanceLevel: 'basic',
      auditScope: 'personal',
      overageBillingEnabled: false,
      customerAuditSurfaces: false,
    },
  },
  pro: {
    planName: 'Pro',
    entitlements: {
      maxRequestsPerMonth: 5_000,
      maxTokensPerMonth: 1_500_000,
      allowedModels: ['qwen-3b', 'qwen-7b'],
      routingTier: 'pro',
      codexPacketHandoff: true,
      usageLedger: true,
      marginDashboard: true,
      treasuryAccess: true,
      governanceLevel: 'enhanced',
      auditScope: 'personal',
      overageBillingEnabled: true,
      customerAuditSurfaces: true,
    },
  },
  enterprise: {
    planName: 'Enterprise',
    entitlements: {
      maxRequestsPerMonth: 100_000,
      maxTokensPerMonth: 50_000_000,
      allowedModels: ['qwen-3b', 'qwen-7b', 'qwen-14b'],
      routingTier: 'enterprise',
      codexPacketHandoff: true,
      usageLedger: true,
      marginDashboard: true,
      treasuryAccess: true,
      governanceLevel: 'full',
      auditScope: 'org',
      overageBillingEnabled: true,
      customerAuditSurfaces: true,
    },
  },
};

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

function isCustomerPlanId(value: unknown): value is CustomerPlanId {
  return value === 'free' || value === 'pro' || value === 'enterprise';
}

function isCustomerAuthProvider(value: unknown): value is CustomerAuthProvider {
  return value === 'email' || value === 'google' || value === 'microsoft' || value === 'github' || value === 'apple';
}

function hashPassword(password: string, salt = randomBytes(16).toString('hex')): { salt: string; hash: string } {
  const hash = scryptSync(password, salt, 64).toString('hex');
  return { salt, hash };
}

function deriveCustomerId(email: string): string {
  return `cust_${createHash('sha256').update(normalizeEmail(email)).digest('hex').slice(0, 16)}`;
}

function buildSession(customer: StoredCustomer, governanceProfile: GovernanceMode): CustomerSession {
  const sessionId = `sess_${randomBytes(16).toString('hex')}`;
  const now = Date.now();
  return {
    sessionId,
    customerId: customer.id,
    ownerId: customer.ownerId,
    email: customer.email,
    planId: customer.planId,
    planName: customer.planName,
    entitlements: customer.entitlements,
    governanceProfile,
    organizationId: customer.organizationId,
    organizationRole: customer.organizationRole,
    createdAt: new Date(now).toISOString(),
    expiresAt: new Date(now + 24 * 60 * 60 * 1000).toISOString(),
  };
}

export class CustomerStore {
  readonly organizations = new OrganizationStore();
  private readonly customers = new Map<string, StoredCustomer>();
  private readonly sessions = new Map<string, CustomerSession>();

  signup(input: CustomerSignupInput): { customer: CustomerRecord; session: CustomerSession } {
    if (!isNonEmptyString(input.email)) {
      throw new Error('CUSTOMER: email is required');
    }

    const email = normalizeEmail(input.email);
    const existing = this.findByEmail(email);
    if (existing) {
      throw new Error('CUSTOMER: account already exists');
    }

    const planId = isCustomerPlanId(input.planId) ? input.planId : 'free';
    const preset = PLAN_PRESETS[planId];
    const now = new Date().toISOString();
    const customerId = deriveCustomerId(email);
    const organization = this.resolveOrganization({
      customerId,
      organizationId: input.organizationId?.trim() || undefined,
      organizationName: input.organizationName?.trim() || undefined,
      billingContactEmail: email,
      planId,
      organizationRole: input.organizationRole ?? 'owner',
    });
    const customer: StoredCustomer = {
      id: customerId,
      ownerId: customerId,
      email,
      displayName: input.displayName?.trim() || undefined,
      authProvider: isCustomerAuthProvider(input.authProvider) ? input.authProvider : 'email',
      authSubject: input.authSubject?.trim() || (input.authProvider && input.authProvider !== 'email' ? email : undefined),
      passwordSalt: undefined,
      passwordHash: undefined,
      planId,
      planName: preset.planName,
      entitlements: this.applyOrganizationEntitlements(preset.entitlements, organization?.id),
      organizationId: organization?.id,
      organizationRole: organization?.role,
      createdAt: now,
      updatedAt: now,
    };

    if (input.password) {
      const hashed = hashPassword(input.password);
      customer.passwordSalt = hashed.salt;
      customer.passwordHash = hashed.hash;
    }

    this.customers.set(customer.id, customer);
    const session = this.issueSession(customer, input.governanceProfile ?? 'balanced');
    return { customer: this.publicRecord(customer), session };
  }

  login(input: CustomerLoginInput): { customer: CustomerRecord; session: CustomerSession } {
    const customer = input.email
      ? this.findByEmail(input.email)
      : input.authSubject
        ? this.findByAuthSubject(isCustomerAuthProvider(input.authProvider) ? input.authProvider : 'google', input.authSubject)
        : undefined;
    if (!customer) {
      throw new Error('CUSTOMER: account not found');
    }

    if (input.password && customer.passwordHash && customer.passwordSalt) {
      const { hash } = hashPassword(input.password, customer.passwordSalt);
      const left = Buffer.from(hash, 'hex');
      const right = Buffer.from(customer.passwordHash, 'hex');
      if (left.length !== right.length || !timingSafeEqual(left, right)) {
        throw new Error('CUSTOMER: invalid credentials');
      }
    } else if (customer.passwordHash && !input.password) {
      throw new Error('CUSTOMER: password required');
    }

    const session = this.issueSession(customer, input.governanceProfile ?? 'balanced');
    return { customer: this.publicRecord(customer), session };
  }

  getSession(sessionId: string): CustomerSession | undefined {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return undefined;
    }
    if (new Date(session.expiresAt).getTime() < Date.now()) {
      this.sessions.delete(sessionId);
      return undefined;
    }
    return session;
  }

  list(): CustomerRecord[] {
    return [...this.customers.values()].map((customer) => this.publicRecord(customer));
  }

  get(customerId: string): CustomerRecord | undefined {
    const customer = this.customers.get(customerId);
    return customer ? this.publicRecord(customer) : undefined;
  }

  getEntitlements(customerId: string): CustomerEntitlements | undefined {
    return this.customers.get(customerId)?.entitlements;
  }

  getOrganization(organizationId: string) {
    return this.organizations.get(organizationId);
  }

  listOrganizations() {
    return this.organizations.list();
  }

  upsertOrganization(input: {
    name: string;
    billingContactEmail: string;
    planId: CustomerPlanId;
    domain?: string;
    ownerCustomerId: string;
    ownerRole?: OrganizationRole;
  }) {
    return this.organizations.create(input);
  }

  private issueSession(customer: StoredCustomer, governanceProfile: GovernanceMode): CustomerSession {
    const session = buildSession(customer, governanceProfile);
    this.sessions.set(session.sessionId, session);
    return session;
  }

  private findByEmail(email: string): StoredCustomer | undefined {
    const normalized = normalizeEmail(email);
    return [...this.customers.values()].find((customer) => customer.email === normalized);
  }

  private findByAuthSubject(provider: CustomerAuthProvider, authSubject: string): StoredCustomer | undefined {
    return [...this.customers.values()].find(
      (customer) => customer.authProvider === provider && customer.authSubject === authSubject.trim(),
    );
  }

  private resolveOrganization(input: {
    customerId: string;
    organizationId?: string;
    organizationName?: string;
    billingContactEmail: string;
    planId: CustomerPlanId;
    organizationRole: OrganizationRole;
  }): { id: string; role: OrganizationRole } | undefined {
    if (input.organizationId) {
      const existing = this.organizations.get(input.organizationId);
      if (existing) {
        this.organizations.addMember(existing.id, {
          customerId: input.customerId,
          role: input.organizationRole,
        });
        return { id: existing.id, role: input.organizationRole };
      }
      const created = this.organizations.upsert({
        id: input.organizationId,
        name: input.organizationName ?? input.organizationId,
        billingContactEmail: input.billingContactEmail,
        planId: input.planId,
        ownerCustomerId: input.customerId,
        ownerRole: input.organizationRole,
      });
      return { id: created.id, role: input.organizationRole };
    }

    if (input.organizationName) {
      const created = this.organizations.create({
        name: input.organizationName,
        billingContactEmail: input.billingContactEmail,
        planId: input.planId,
        ownerCustomerId: input.customerId,
        ownerRole: input.organizationRole,
      });
      return { id: created.id, role: input.organizationRole };
    }

    return undefined;
  }

  private applyOrganizationEntitlements(entitlements: CustomerEntitlements, organizationId?: string): CustomerEntitlements {
    if (!organizationId) {
      return entitlements;
    }
    return {
      ...entitlements,
      auditScope: 'org',
      customerAuditSurfaces: true,
      overageBillingEnabled: true,
    };
  }

  private publicRecord(customer: StoredCustomer): CustomerRecord {
    const { passwordSalt: _passwordSalt, passwordHash: _passwordHash, ...record } = customer;
    return record;
  }
}
