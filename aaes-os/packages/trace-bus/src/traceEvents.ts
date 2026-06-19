import type { InvariantId, RunId, SpanId } from '@aaes-os/runledger';

/** Structural fault payload — mirrors @aaes-os/aaes-governance FaultEvent without package cycle. */
export interface TraceFaultPayload {
  faultId: string;
  runId: RunId;
  spanId: SpanId;
  invariantId?: InvariantId;
  timestamp: string;
  faultCode: string;
  severity: string;
  contextSnapshot?: unknown;
  recurrenceCount?: number;
}

export type TraceEventType =
  | 'TRACE_SPAN_START'
  | 'TRACE_SPAN_END'
  | 'TRACE_INVARIANT'
  | 'TRACE_FAULT'
  | 'TRACE_RUN_START'
  | 'TRACE_RUN_END';

/** Event type emitted when an invariant records a fault. */
export const TRACE_FAULT: TraceEventType = 'TRACE_FAULT';

export interface TraceEventBase {
  type: TraceEventType;
  timestamp: string;
  runId: RunId;
  spanId?: SpanId;
  runtimeContext?: {
    hashAlg?: string;
    hLawSpine?: string;
    hCorridors?: string;
    hTrustRoot?: string;
  };
}

export interface TraceSpanEvent extends TraceEventBase {
  type: 'TRACE_SPAN_START' | 'TRACE_SPAN_END';
  name: string;
}

export interface TraceRunEvent extends TraceEventBase {
  type: 'TRACE_RUN_START' | 'TRACE_RUN_END';
}

export interface TraceInvariantEvent extends TraceEventBase {
  type: 'TRACE_INVARIANT';
  invariantId: InvariantId;
  passed: boolean;
  message?: string;
}

export interface TraceFaultEvent extends TraceEventBase {
  type: 'TRACE_FAULT';
  fault: TraceFaultPayload;
}

export type TraceEvent =
  | TraceSpanEvent
  | TraceRunEvent
  | TraceInvariantEvent
  | TraceFaultEvent;

export type TraceListener = (event: TraceEvent) => void;

export type TraceUnsubscribe = () => void;
