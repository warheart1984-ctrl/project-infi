/**
 * Mythic: Trace vault
 * Engineering: InMemoryGovernedTraceStore
 */

import type { TraceEvent } from "./types.js";

export interface TraceStore {
  append(event: TraceEvent): void;
  getEventsBySpan(span_id: string): TraceEvent[];
}

/** In-memory append-only store for v0.1 proof. */
export class InMemoryTraceStore implements TraceStore {
  private readonly events: TraceEvent[] = [];

  append(event: TraceEvent): void {
    this.events.push(event);
  }

  getEventsBySpan(span_id: string): TraceEvent[] {
    return this.events.filter((event) => event.span_id === span_id);
  }
}
