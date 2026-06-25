import type { RunContext } from '../types.js';

export interface InvariantContext {
  run: RunContext;
  result?: unknown;
}

export interface InvariantResult {
  ok: boolean;
  invariantId?: string;
  message?: string;
}

export interface Invariant {
  id: string;
  description: string;
  check(ctx: InvariantContext): InvariantResult;
}
