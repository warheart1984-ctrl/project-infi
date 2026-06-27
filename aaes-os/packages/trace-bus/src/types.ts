import type { RunId, SpanId } from '@aaes-os/runledger';

export type TraceEventType =
  | 'TRACE_START'
  | 'TRACE_STEP'
  | 'TRACE_DECISION'
  | 'TRACE_FAULT'
  | 'TRACE_PATCH'
  | 'TRACE_END'
  | 'TRACE_INVARIANT'
  | 'TRACE_SPAN'
  | 'TRACE_RUN';

export interface TraceEvent {
  type: TraceEventType;
  runId: RunId;
  spanId?: SpanId;
  timestamp: string;
  payload: unknown;
}

export type TraceSubscriber = (event: TraceEvent) => void;

export type TraceUnsubscribe = () => void;
