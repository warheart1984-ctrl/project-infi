import type { FaultEvent } from './faultTypes.js';

export interface PatternRecord {
  patternId: string;
  faultCodes: string[];
  invariantIds?: string[];
  recurrence: number;
  firstSeenAt: string;
  lastSeenAt: string;
  associatedPatches?: string[];
  effectivenessScore?: number;
}

/** PatternLedger — clusters recurring faults by code + invariant. */
export class PatternLedger {
  private readonly patterns = new Map<string, PatternRecord>();

  ingestFault(event: FaultEvent): void {
    const key = this.buildKey(event.faultCode, event.invariantId);
    const existing = this.patterns.get(key);

    if (!existing) {
      const record: PatternRecord = {
        patternId: key,
        faultCodes: [event.faultCode],
        invariantIds: event.invariantId ? [event.invariantId] : [],
        recurrence: 1,
        firstSeenAt: event.timestamp,
        lastSeenAt: event.timestamp,
      };
      this.patterns.set(key, record);
      return;
    }

    existing.recurrence += 1;
    existing.lastSeenAt = event.timestamp;
    this.patterns.set(key, existing);
  }

  getAll(): PatternRecord[] {
    return [...this.patterns.values()];
  }

  getTopRecurring(limit = 10): PatternRecord[] {
    return this.getAll()
      .sort((a, b) => b.recurrence - a.recurrence)
      .slice(0, limit);
  }

  private buildKey(faultCode: string, invariantId?: string): string {
    return invariantId ? `${faultCode}::${invariantId}` : faultCode;
  }
}
