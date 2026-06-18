/**
 * Mythic: Trace vault
 * Engineering: TraceStore
 */

import type { AAESContext, AAESStep } from "../types.js";

export interface TraceRecord {
  traceId: string;
  steps: AAESStep[];
}

export interface TraceStore {
  appendStep(ctx: AAESContext, step: AAESStep): void;
  getTrace(traceId: string): TraceRecord | undefined;
}

/** In-memory append-only trace store for v1. */
export class InMemoryTraceStore implements TraceStore {
  private readonly traces = new Map<string, AAESStep[]>();

  appendStep(ctx: AAESContext, step: AAESStep): void {
    const existing = this.traces.get(ctx.traceId) ?? [];
    existing.push({ ...step });
    this.traces.set(ctx.traceId, existing);
  }

  getTrace(traceId: string): TraceRecord | undefined {
    const steps = this.traces.get(traceId);
    if (!steps) {
      return undefined;
    }
    return { traceId, steps: [...steps] };
  }
}
