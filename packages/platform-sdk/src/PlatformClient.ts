import type {
  AuthSession,
  CapabilityRecord,
  CustomerRecord,
  CustomerSession,
  CustomerSignupInput,
  CustomerLoginInput,
  GovernanceMode,
  GovernanceProfile,
  InvokeResult,
  OrgMember,
  OrganizationRecord,
  OverageEvent,
  UsageRecord,
} from '@aaes-os/platform-core';

export interface PlatformClientOptions {
  baseUrl: string;
  apiKey?: string;
  sessionId?: string;
  governanceProfile?: GovernanceMode;
}

export class PlatformClient {
  private apiKey?: string;
  private sessionId?: string;
  private governanceProfile: GovernanceMode;

  constructor(private readonly options: PlatformClientOptions) {
    this.apiKey = options.apiKey;
    this.sessionId = options.sessionId;
    this.governanceProfile = options.governanceProfile ?? 'balanced';
  }

  get baseUrl(): string {
    return this.options.baseUrl.replace(/\/$/, '');
  }

  async login(ownerId: string, governanceProfile?: GovernanceMode): Promise<AuthSession> {
    const session = await this.request<AuthSession>('POST', '/v1/auth/login', {
      ownerId,
      governanceProfile: governanceProfile ?? this.governanceProfile,
    });
    this.sessionId = session.sessionId;
    this.governanceProfile = session.governanceProfile;
    return session;
  }

  async signupCustomer(input: CustomerSignupInput): Promise<{ customer: CustomerRecord; session: CustomerSession }> {
    const result = await this.request<{ customer: CustomerRecord; session: CustomerSession }>('POST', '/v1/customers/signup', input);
    this.sessionId = result.session.sessionId;
    this.governanceProfile = result.session.governanceProfile;
    return result;
  }

  async loginCustomer(input: CustomerLoginInput): Promise<{ customer: CustomerRecord; session: CustomerSession }> {
    const result = await this.request<{ customer: CustomerRecord; session: CustomerSession }>('POST', '/v1/customers/login', input);
    this.sessionId = result.session.sessionId;
    this.governanceProfile = result.session.governanceProfile;
    return result;
  }

  async getCurrentCustomer(): Promise<{ customer: CustomerRecord; entitlements: CustomerRecord['entitlements']; planId: string; planName: string }> {
    return this.governedRequest('GET', '/v1/customers/me');
  }

  async listCustomers(): Promise<{ customers: CustomerRecord[] }> {
    return this.governedRequest('GET', '/v1/customers');
  }

  async createOrg(input: {
    name: string;
    billingContactEmail?: string;
    planId?: string;
    domain?: string;
    ownerRole?: string;
  }): Promise<{ organization: OrganizationRecord }> {
    return this.governedRequest('POST', '/v1/organizations', input);
  }

  async listOrgs(): Promise<{ organizations: OrganizationRecord[] }> {
    return this.governedRequest('GET', '/v1/organizations');
  }

  async getOrg(orgId: string): Promise<{ organization: OrganizationRecord }> {
    return this.governedRequest('GET', `/v1/organizations/${orgId}`);
  }

  async listOrgMembers(orgId: string): Promise<{ organizationId: string; members: OrgMember[] }> {
    return this.governedRequest('GET', `/v1/organizations/${orgId}/members`);
  }

  async addOrgMember(orgId: string, customerId: string, role: string): Promise<{ organization: OrganizationRecord }> {
    return this.governedRequest('POST', `/v1/organizations/${orgId}/members`, { customerId, role });
  }

  async updateOrgMemberRole(orgId: string, customerId: string, role: string): Promise<{ organization: OrganizationRecord }> {
    return this.governedRequest('PATCH', `/v1/organizations/${orgId}/members/${customerId}`, { role });
  }

  async getUsageSummary(): Promise<{ totalUnits: number; byOperation: Record<string, number>; byProfile: Record<GovernanceMode, number> }> {
    return this.governedRequest('GET', '/v1/billing/usage');
  }

  async getCustomerQuota(): Promise<{
    customer: CustomerRecord;
    usageRecords: UsageRecord[];
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
  }> {
    return this.governedRequest('GET', '/v1/customers/quota');
  }

  async getOrgUsage(orgId: string): Promise<{
    organizationId: string;
    total: number;
    byKind: Record<string, number>;
    summary: { total: number; byKind: Record<string, number> };
    overageEvents: OverageEvent[];
  }> {
    return this.governedRequest('GET', `/v1/organizations/${orgId}/usage`);
  }

  async recordOrgUsage(orgId: string, input: { customerId?: string; kind: string; amount: number; metadata?: Record<string, unknown> }): Promise<UsageRecord> {
    return this.governedRequest('POST', `/v1/organizations/${orgId}/usage`, input);
  }

  async getOverageEvents(orgId: string): Promise<{ events: OverageEvent[] }> {
    return this.governedRequest('GET', `/v1/organizations/${orgId}/overage`);
  }

  setApiKey(key: string): void {
    this.apiKey = key;
    this.sessionId = undefined;
  }

  async createApiKey(label: string, governanceProfile?: GovernanceMode) {
    return this.request<{ record: { id: string }; key: string }>('POST', '/v1/auth/keys', {
      label,
      governanceProfile,
    });
  }

  async listApiKeys() {
    return this.request<Array<{ id: string; label: string; keyPrefix: string }>>(
      'GET',
      '/v1/auth/keys',
    );
  }

  async listGovernanceProfiles(): Promise<GovernanceProfile[]> {
    return this.request('GET', '/v1/governance/profiles');
  }

  async publishCapability(input: {
    id: string;
    name: string;
    description?: string;
    organId: string;
    version: string;
    changelog?: string;
  }): Promise<CapabilityRecord> {
    return this.request('POST', '/v1/capabilities/publish', input);
  }

  async invokeCapability(
    capabilityId: string,
    input: Record<string, unknown>,
    version?: string,
  ): Promise<InvokeResult> {
    return this.governedRequest('POST', `/v1/capabilities/${capabilityId}/invoke`, {
      input,
      version,
    });
  }

  async getUsage() {
    return this.request<{
      totalUnits: number;
      byOperation: Record<string, number>;
      byProfile: Record<GovernanceMode, number>;
    }>('GET', '/v1/billing/usage');
  }

  async getTreasuryPlan(input?: {
    customerId?: string;
    customerInvoiceUsd?: number;
    openAiUsageCostUsd?: number;
    taxRatePct?: number;
    profitReservePct?: number;
    platformReservePct?: number;
  }) {
    return this.governedRequest('POST', '/v1/billing/treasury/plan', {
      ...(input ?? {}),
    });
  }

  async getTreasurySchedule() {
    return this.governedRequest('GET', '/v1/billing/treasury/schedule');
  }

  async createCheckoutSession(orgId: string, input?: { amount?: number; currency?: string }) {
    return this.governedRequest('POST', `/v1/organizations/${orgId}/billing/checkout`, input ?? {});
  }

  async createPayoutInstruction(orgId: string, input?: { amount?: number; currency?: string }) {
    return this.governedRequest('POST', `/v1/organizations/${orgId}/billing/payout`, input ?? {});
  }

  async getPricingAudit(orgId: string) {
    return this.governedRequest('GET', `/v1/organizations/${orgId}/audit/pricing`);
  }

  async getRoutingAudit(orgId: string) {
    return this.governedRequest('GET', `/v1/organizations/${orgId}/audit/routing`);
  }

  async getEntitlementsAudit(orgId: string) {
    return this.governedRequest('GET', `/v1/organizations/${orgId}/audit/entitlements`);
  }

  async evaluatePricing(input: {
    customerId?: string;
    segment: string;
    monthlyCustomers?: number;
    routedRequestsPerCustomer?: number;
    governanceReviewsPerCustomer?: number;
    knowledgeUpdatesPerCustomer?: number;
    serviceHoursPerCustomer?: number;
    compliancePressure?: number;
    workloadVolatility?: number;
    supportComplexity?: number;
    privateDeployment?: boolean;
    assuranceRequired?: boolean;
    customerInvoiceUsd?: number;
    openAiUsageCostUsd?: number;
    taxRatePct?: number;
    profitReservePct?: number;
    platformReservePct?: number;
  }) {
    return this.governedRequest('POST', '/v1/billing/pricing/evaluate', input);
  }

  async testModule(moduleId: string, version: string) {
    return this.request<{ passed: boolean; checks: string[] }>('POST', '/v1/modules/test', {
      moduleId,
      version,
    });
  }

  async discoverOrganisms(filter?: { capability?: string; governanceProfile?: GovernanceMode }) {
    const params = new URLSearchParams();
    if (filter?.capability) params.set('capability', filter.capability);
    if (filter?.governanceProfile) params.set('governanceProfile', filter.governanceProfile);
    const qs = params.toString();
    return this.request('GET', `/v1/mesh/discover${qs ? `?${qs}` : ''}`);
  }

  async connectOrganism(organismId: string, scope?: string[]) {
    return this.request('POST', '/v1/mesh/connect', { organismId, scope });
  }

  async runWorkflow(steps: Array<{ organismId: string; capabilityId: string; input: Record<string, unknown> }>) {
    return this.governedRequest('POST', '/v1/workflows/run', { steps });
  }

  /** Governance-safe wrapper — attaches trace metadata and validates profile context */
  private async governedRequest<T>(
    method: string,
    path: string,
    body?: Record<string, unknown>,
  ): Promise<T> {
    return this.request<T>(method, path, {
      ...body,
      _governance: {
        profile: this.governanceProfile,
        traceId: `sdk-${Date.now().toString(36)}`,
      },
    });
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<T> {
    const headers: Record<string, string> = { 'content-type': 'application/json' };
    if (this.apiKey) {
      headers.authorization = `Bearer ${this.apiKey}`;
    } else if (this.sessionId) {
      headers['x-session-id'] = this.sessionId;
    }

    const res = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });

    if (!res.ok) {
      const err = (await res.json().catch(() => ({ error: res.statusText }))) as { error?: string };
      throw new Error(err.error ?? `HTTP ${res.status}`);
    }

    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  }
}

export { PlatformClient as default };
