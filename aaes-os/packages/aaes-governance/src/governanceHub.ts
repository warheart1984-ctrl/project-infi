import { FaultJournal } from './faultJournal.js';
import { InvariantEngine } from './invariantEngine.js';
import { DeterminismInvariant } from './invariants/determinism.js';
import { OutputShapeInvariant } from './invariants/outputShape.js';
import { PatternLedger } from './patternLedger.js';
import type { FaultEvent } from './faultTypes.js';
import type { GovernanceTraceBus } from './tracePort.js';

export function createMinimalInvariantEngine(
  faultJournal?: FaultJournal,
  traceBus?: GovernanceTraceBus,
): { engine: InvariantEngine; journal: FaultJournal } {
  const journal = faultJournal ?? new FaultJournal();
  const engine = new InvariantEngine(journal, traceBus);
  engine.register(new OutputShapeInvariant());
  engine.register(new DeterminismInvariant());
  return { engine, journal };
}

export function syncPatternsFromJournal(journal: FaultJournal, ledger: PatternLedger): void {
  for (const fault of journal.getAll()) {
    ledger.ingestFault(fault);
  }
}

export interface GovernanceHubOptions {
  journal?: FaultJournal;
  patternLedger?: PatternLedger;
  traceBus?: GovernanceTraceBus;
}

/** Wires PatternLedger ingestion to TRACE_FAULT events on a shared bus. */
export class GovernanceHub {
  readonly journal: FaultJournal;
  readonly patternLedger: PatternLedger;
  private readonly unsubscribe?: () => void;

  constructor(options: GovernanceHubOptions = {}) {
    this.journal = options.journal ?? new FaultJournal();
    this.patternLedger = options.patternLedger ?? new PatternLedger();

    if (options.traceBus) {
      this.unsubscribe = options.traceBus.subscribe((event) => {
        if (event.type === 'TRACE_FAULT') {
          this.patternLedger.ingestFault(event.fault);
        }
      });
    }
  }

  ingestFaultFromEvent(fault: FaultEvent): void {
    this.patternLedger.ingestFault(fault);
  }

  dispose(): void {
    this.unsubscribe?.();
  }
}

export function countInvariantFaults(
  faults: FaultEvent[],
  invariantId: string,
): number {
  return faults.filter(
    (fault) => fault.invariantId === invariantId || fault.faultCode.includes(invariantId),
  ).length;
}

export function countSpanBoundaryFaults(faults: FaultEvent[]): number {
  return faults.filter(
    (fault) =>
      fault.faultCode === 'SPAN_ORPHAN' ||
      fault.faultCode === 'INV_FAIL_SPAN_BOUNDARY' ||
      hasReason(fault.contextSnapshot, 'span_orphan'),
  ).length;
}

function hasReason(value: unknown, reason: string): boolean {
  return (
    typeof value === 'object' &&
    value !== null &&
    'reason' in value &&
    (value as { reason?: unknown }).reason === reason
  );
}
