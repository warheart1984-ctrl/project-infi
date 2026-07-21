import type { OverageEvent, UsageEvent } from '../types.js';

export interface UsageStore {
  recordUsage(event: {
    orgId: string;
    customerId?: string;
    kind: string;
    amount: number;
    metadata?: Record<string, unknown>;
  }): Promise<UsageEvent>;

  getUsageSummary(orgId: string): Promise<{
    total: number;
    byKind: Record<string, number>;
  }>;

  recordOverage(event: {
    orgId: string;
    kind: string;
    amount: number;
    metadata?: Record<string, unknown>;
  }): Promise<OverageEvent>;

  listOverageEvents(orgId: string): Promise<OverageEvent[]>;
}

export interface QuotaEnforcementResult {
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
}

export interface UsageQuotaPlan {
  limit: number;
  used: number;
  overage: number;
  overageBillingUsd: number;
  status: 'within_limit' | 'metered_overage' | 'blocked';
  allowed: boolean;
  reason: string;
}
