import type { GovernanceMode, OverageEvent, UsageRecord } from '../types.js';

export interface BillingHook {
  onUsage(record: UsageRecord): void | Promise<void>;
}

export interface MeterOptions {
  hooks?: BillingHook[];
}

const TIER_MULTIPLIERS: Record<GovernanceMode, number> = {
  strict: 2.0,
  balanced: 1.0,
  experimental: 0.5,
};

export class UsageMeter {
  private readonly records: UsageRecord[] = [];
  private readonly overages: OverageEvent[] = [];
  private readonly hooks: BillingHook[];

  constructor(options: MeterOptions = {}) {
    this.hooks = options.hooks ?? [];
  }

  record(input: Omit<UsageRecord, 'id' | 'timestamp'>): UsageRecord {
    const entry: UsageRecord = {
      ...input,
      id: `usage_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
      timestamp: new Date().toISOString(),
    };
    this.records.push(entry);
    for (const hook of this.hooks) {
      void hook.onUsage(entry);
    }
    return entry;
  }

  recordOverage(input: Omit<OverageEvent, 'id' | 'occurredAt'>): OverageEvent {
    const entry: OverageEvent = {
      ...input,
      id: `overage_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
      occurredAt: new Date().toISOString(),
    };
    this.overages.push(entry);
    return entry;
  }

  computeUnits(
    operation: string,
    baseUnits: number,
    governanceProfile: GovernanceMode,
  ): number {
    const multiplier = TIER_MULTIPLIERS[governanceProfile];
    const opFactor = operation.includes('invoke') ? 1 : operation.includes('mesh') ? 1.5 : 0.25;
    return Math.ceil(baseUnits * multiplier * opFactor);
  }

  summary(ownerId: string): {
    totalUnits: number;
    byOperation: Record<string, number>;
    byProfile: Record<GovernanceMode, number>;
  } {
    const filtered = this.records.filter((r) => r.ownerId === ownerId);
    const byOperation: Record<string, number> = {};
    const byProfile: Record<GovernanceMode, number> = {
      strict: 0,
      balanced: 0,
      experimental: 0,
    };
    let totalUnits = 0;

    for (const r of filtered) {
      totalUnits += r.units;
      byOperation[r.operation] = (byOperation[r.operation] ?? 0) + r.units;
      byProfile[r.governanceProfile] += r.units;
    }

    return { totalUnits, byOperation, byProfile };
  }

  usageSummary(orgId: string): {
    total: number;
    byKind: Record<string, number>;
  } {
    const filtered = this.records.filter((record) => record.orgId === orgId);
    const byKind: Record<string, number> = {};
    let total = 0;
    for (const record of filtered) {
      total += record.units;
      const kind = record.operation;
      byKind[kind] = (byKind[kind] ?? 0) + record.units;
    }
    return { total, byKind };
  }

  listOverages(orgId: string): OverageEvent[] {
    return this.overages.filter((record) => record.orgId === orgId).map((record) => ({ ...record }));
  }

  allRecords(): UsageRecord[] {
    return [...this.records];
  }
}
