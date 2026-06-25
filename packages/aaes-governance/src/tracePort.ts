import type { InvariantId, RunId, SpanId } from '@aaes-os/runledger';

import type { FaultEvent } from './faultTypes.js';

export interface InvariantTraceEvent {
  type: 'TRACE_INVARIANT';
  timestamp: string;
  runId: RunId;
  spanId: SpanId;
  invariantId: InvariantId;
  passed: boolean;
  message?: string;
}

export interface FaultTraceEvent {
  type: 'TRACE_FAULT';
  timestamp: string;
  runId: RunId;
  spanId: SpanId;
  fault: FaultEvent;
}

export type GovernanceTraceEvent = InvariantTraceEvent | FaultTraceEvent;

/** Minimal trace port — implemented by @aaes-os/trace-bus TraceBus at runtime. */
export interface GovernanceTraceBus {
  emit(event: GovernanceTraceEvent): void;
  subscribe(listener: (event: GovernanceTraceEvent) => void): () => void;
}
