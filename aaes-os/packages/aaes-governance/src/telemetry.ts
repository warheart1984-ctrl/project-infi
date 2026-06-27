import { DriftMetrics, type DriftScore } from './driftMetrics.js';
import { FaultJournal } from './faultJournal.js';
import { PatternLedger, type PatternRecord } from './patternLedger.js';
import { syncPatternsFromJournal } from './governanceHub.js';
import type { FaultEvent } from './faultTypes.js';
import { initGovernanceGlobals } from './bootstrap.js';

export interface TelemetrySnapshot {
  drift: DriftScore;
  topPatterns: PatternRecord[];
  lastFaults: FaultEvent[];
}

function resolveStores(): { journal: FaultJournal; patterns: PatternLedger } {
  if (globalThis.faultJournal && globalThis.patternLedger) {
    return { journal: globalThis.faultJournal, patterns: globalThis.patternLedger };
  }
  return initGovernanceGlobals();
}

/** Collect drift, top patterns, and recent faults from governance globals. */
export function collectTelemetrySnapshot(limit = 10): TelemetrySnapshot {
  const { journal, patterns } = resolveStores();
  const faults = journal.getAll();

  if (patterns.getAll().length === 0 && faults.length > 0) {
    syncPatternsFromJournal(journal, patterns);
  }

  const patternRecords = patterns.getAll();
  const drift = new DriftMetrics().computeDrift(faults, patternRecords);

  return {
    drift,
    topPatterns: patterns.getTopRecurring(5),
    lastFaults: faults.slice(-limit).reverse(),
  };
}
