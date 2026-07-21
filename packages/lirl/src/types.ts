export const LIRL_ALLOWED_ACTIONS = ['memory.write', 'ping', 'observe'] as const;

export type LirlAction = (typeof LIRL_ALLOWED_ACTIONS)[number];

export interface LirlIntent {
  /** Stable id for this intent (caller may omit; loop assigns UUID). */
  intentId?: string;
  /** Who is requesting the action. */
  actorId: string;
  /** Requested action under LIRL law. */
  action: string;
  /** Action payload (required for memory.write). */
  payload?: {
    key?: string;
    value?: unknown;
    [key: string]: unknown;
  };
  /** If true, intent attempts to bypass law — always rejected. */
  forceBypass?: boolean;
  metadata?: Record<string, unknown>;
}

export type LirlVerdict = 'ACCEPT' | 'REJECT';

export interface LirlGateResult {
  verdict: LirlVerdict;
  reasons: string[];
  invariantResults: Array<{ invariantId?: string; passed: boolean; message?: string }>;
  runId: string;
  spanId: string;
}

export interface LirlLoopResult {
  intentId: string;
  verdict: LirlVerdict;
  reasons: string[];
  runId: string;
  spanId: string;
  receiptId: string;
  memoryWritten: boolean;
  memoryKey?: string;
  operatorView: LirlOperatorSnapshot;
}

export interface LirlOperatorSnapshot {
  verdict: LirlVerdict;
  receiptId: string;
  intentId: string;
  actorId: string;
  action: string;
  memoryWritten: boolean;
  reasons: string[];
  issuedAt: string;
  html: string;
}
