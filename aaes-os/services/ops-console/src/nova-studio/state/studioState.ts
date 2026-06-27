import type { StudioMode } from '../routes.js';

export type SkillzMcgeeReceipt = {
  id: string;
  timestamp: string;
  actor: string;
  slice: string;
  input?: unknown;
  output?: unknown;
  status: string;
};

export type SkillzMcgeeSliceState = {
  last_status: string;
  last_output: unknown;
  last_run_id: string;
};

export type SkillzMcgeeCapability = {
  name: string;
  description: string;
  governed: boolean;
  receiptRequired: boolean;
};

export type SkillzMcgeeLedgerSummary = {
  source: string;
  available: boolean;
  receiptCount: number;
  state: Record<string, SkillzMcgeeSliceState>;
  recentReceipts: SkillzMcgeeReceipt[];
  capabilities: SkillzMcgeeCapability[];
  error?: string;
};

export type ContinuityState = {
  checkpoint: string;
  receiptCount: number;
};

export type GovernanceStatus = {
  status: 'pending' | 'ok' | 'error';
  invariantFailures: string[];
};

export type SubstrateHealth = {
  ledgerAvailable: boolean;
  receiptCount: number;
};

export type OperatorContext = {
  operatorId: string;
  mode: StudioMode;
  continuity: ContinuityState;
  activeSlice: string | null;
  governance: GovernanceStatus;
  substrateHealth: SubstrateHealth;
};

export type EnforcementSummary = {
  status: string;
  events: { receiptId: string; verdict: string; reasonCode: string; transitionId?: string }[];
  invariantSet?: { active: number; disabled: number };
  tokenCounts?: Record<string, number>;
  enforcementRatePerMinute?: number;
  replayAttemptsBlocked?: number;
};

export function createOperatorContext(input: {
  operatorId: string;
  mode: StudioMode;
  skillzmcgee: SkillzMcgeeLedgerSummary;
  invariantFailures?: string[];
}): OperatorContext {
  const latestReceipt = input.skillzmcgee.recentReceipts[0];
  return {
    operatorId: input.operatorId,
    mode: input.mode,
    continuity: {
      checkpoint: latestReceipt ? `receipt:${latestReceipt.id}` : 'receipt:none',
      receiptCount: input.skillzmcgee.receiptCount,
    },
    activeSlice: latestReceipt?.slice ?? null,
    governance: {
      status: input.invariantFailures?.length ? 'error' : 'pending',
      invariantFailures: input.invariantFailures ?? [],
    },
    substrateHealth: {
      ledgerAvailable: input.skillzmcgee.available,
      receiptCount: input.skillzmcgee.receiptCount,
    },
  };
}
