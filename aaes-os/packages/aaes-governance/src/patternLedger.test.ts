import { describe, expect, it } from 'vitest';

import { asInvariantId, asRunId, asSpanId } from '@aaes-os/runledger';

import { PatternLedger } from './patternLedger.js';
import { FaultJournal } from './faultJournal.js';

describe('PatternLedger', () => {
  it('increments recurrence for the same fault code', () => {
    const ledger = new PatternLedger();
    const journal = new FaultJournal();
    const runId = asRunId('run-1');
    const spanId = asSpanId('span-1');

    const fault1 = journal.recordFault({
      runId,
      spanId,
      invariantId: asInvariantId('INV_OUTPUT_SHAPE'),
      faultCode: 'INV_FAIL_INV_OUTPUT_SHAPE',
      severity: 'ERROR',
    });
    const fault2 = journal.recordFault({
      runId,
      spanId,
      invariantId: asInvariantId('INV_OUTPUT_SHAPE'),
      faultCode: 'INV_FAIL_INV_OUTPUT_SHAPE',
      severity: 'ERROR',
    });

    ledger.ingestFault(fault1);
    ledger.ingestFault(fault2);

    const top = ledger.getTopRecurring(1);
    expect(top).toHaveLength(1);
    expect(top[0]?.recurrence).toBe(2);
  });
});
