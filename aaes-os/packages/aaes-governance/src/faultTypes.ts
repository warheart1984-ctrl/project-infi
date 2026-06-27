import type { InvariantId, RunId, SpanId } from '@aaes-os/runledger';

export type Severity = 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';

export type FaultId = string & { readonly __brand: 'FaultId' };

export function asFaultId(value: string): FaultId {
  return value as FaultId;
}

export interface FaultEvent {
  faultId: FaultId;
  runId: RunId;
  spanId: SpanId;
  invariantId?: InvariantId;
  timestamp: string;
  faultCode: string;
  severity: Severity;
  contextSnapshot?: unknown;
  patchApplied?: string;
  recurrenceCount?: number;
}

export interface RecordFaultInput {
  runId: RunId;
  spanId: SpanId;
  invariantId?: InvariantId;
  faultCode: string;
  severity: Severity;
  contextSnapshot?: unknown;
  patchApplied?: string;
}
