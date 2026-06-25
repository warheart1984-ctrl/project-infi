import { FaultJournal } from './faultJournal.js';
import { PatternLedger } from './patternLedger.js';
import type { FaultEvent, RecordFaultInput } from './faultTypes.js';

/** Initialize process-wide governance singletons on `globalThis`. */
export function initGovernanceGlobals(): { journal: FaultJournal; patterns: PatternLedger } {
  if (!globalThis.faultJournal) {
    globalThis.faultJournal = new FaultJournal();
  }
  if (!globalThis.patternLedger) {
    globalThis.patternLedger = new PatternLedger();
  }
  return { journal: globalThis.faultJournal, patterns: globalThis.patternLedger };
}

/** Record a fault and ingest the matching pattern in one step. */
export function recordFaultWithPattern(input: RecordFaultInput): FaultEvent {
  const { journal } = initGovernanceGlobals();
  return journal.recordFault(input);
}
