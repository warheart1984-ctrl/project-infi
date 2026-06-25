import { randomUUID } from 'node:crypto';

import type { InvariantId } from '@aaes-os/runledger';

import { asFaultId, type FaultEvent, type RecordFaultInput } from './faultTypes.js';

function recurrenceKey(faultCode: string, invariantId?: InvariantId): string {
  return invariantId ? `${faultCode}::${invariantId}` : faultCode;
}

/** In-memory fault journal — v0.1 spine primitive. */
export class FaultJournal {
  private readonly events: FaultEvent[] = [];
  private readonly recurrenceCounts = new Map<string, number>();

  recordFault(input: RecordFaultInput): FaultEvent {
    const key = recurrenceKey(input.faultCode, input.invariantId);
    const recurrenceCount = (this.recurrenceCounts.get(key) ?? 0) + 1;
    this.recurrenceCounts.set(key, recurrenceCount);

    const event: FaultEvent = {
      faultId: asFaultId(randomUUID()),
      runId: input.runId,
      spanId: input.spanId,
      invariantId: input.invariantId,
      timestamp: new Date().toISOString(),
      faultCode: input.faultCode,
      severity: input.severity,
      contextSnapshot: input.contextSnapshot,
      recurrenceCount,
    };
    this.events.push(event);
    globalThis.patternLedger?.ingestFault(event);
    return structuredClone(event);
  }

  getAll(): FaultEvent[] {
    return this.events.map((event) => structuredClone(event));
  }

  getByRun(runId: FaultEvent['runId']): FaultEvent[] {
    return this.events
      .filter((event) => event.runId === runId)
      .map((event) => structuredClone(event));
  }

  getBySpan(spanId: FaultEvent['spanId']): FaultEvent[] {
    return this.events
      .filter((event) => event.spanId === spanId)
      .map((event) => structuredClone(event));
  }

  getByFaultCode(faultCode: string): FaultEvent[] {
    return this.events
      .filter((event) => event.faultCode === faultCode)
      .map((event) => structuredClone(event));
  }

  countRecurrence(faultCode: string, invariantId?: InvariantId): number {
    return this.recurrenceCounts.get(recurrenceKey(faultCode, invariantId)) ?? 0;
  }

  /** Alias used by invariant-engine tests. */
  getRecurrence(faultCode: string, invariantId?: InvariantId): number {
    return this.countRecurrence(faultCode, invariantId);
  }

  clear(): void {
    this.events.length = 0;
    this.recurrenceCounts.clear();
  }
}
