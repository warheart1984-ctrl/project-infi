import type { RunId, SpanId } from '@aaes-os/runledger';

import type { TraceEvent, TraceListener, TraceUnsubscribe } from './traceEvents.js';

function now(): string {
  return new Date().toISOString();
}

/** TraceBus v0.1 — pub/sub for governed trace events. */
export class TraceBus {
  private readonly listeners: TraceListener[] = [];
  private readonly log: TraceEvent[] = [];

  subscribe(listener: TraceListener): TraceUnsubscribe {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index >= 0) {
        this.listeners.splice(index, 1);
      }
    };
  }

  emit(event: TraceEvent): TraceEvent {
    this.log.push(event);
    for (const listener of this.listeners) {
      listener(event);
    }
    return event;
  }

  getLog(): readonly TraceEvent[] {
    return [...this.log];
  }

  clear(): void {
    this.log.length = 0;
  }

  spanStart(runId: RunId, spanId: SpanId, name: string): void {
    this.emit({
      type: 'TRACE_SPAN_START',
      timestamp: now(),
      runId,
      spanId,
      name,
    });
  }

  spanEnd(runId: RunId, spanId: SpanId, name: string): void {
    this.emit({
      type: 'TRACE_SPAN_END',
      timestamp: now(),
      runId,
      spanId,
      name,
    });
  }

  runStart(runId: RunId): void {
    this.emit({
      type: 'TRACE_RUN_START',
      timestamp: now(),
      runId,
    });
  }

  runEnd(runId: RunId): void {
    this.emit({
      type: 'TRACE_RUN_END',
      timestamp: now(),
      runId,
    });
  }
}
