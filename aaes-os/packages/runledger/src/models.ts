/** Branded identifiers — causal spine for run/span/invariant linkage. */

export type RunId = string & { readonly __brand: 'RunId' };
export type SpanId = string & { readonly __brand: 'SpanId' };
export type InvariantId = string & { readonly __brand: 'InvariantId' };

export function asRunId(value: string): RunId {
  return value as RunId;
}

export function asSpanId(value: string): SpanId {
  return value as SpanId;
}

export function asInvariantId(value: string): InvariantId {
  return value as InvariantId;
}

export interface RunRecord {
  runId: RunId;
  startedAt: string;
  endedAt?: string;
  metadata?: Record<string, unknown>;
}

export interface SpanRecord {
  spanId: SpanId;
  runId: RunId;
  parentSpanId?: SpanId;
  name: string;
  startedAt: string;
  endedAt?: string;
  invariantIds?: InvariantId[];
}

export interface InvariantLink {
  spanId: SpanId;
  invariantId: InvariantId;
}
