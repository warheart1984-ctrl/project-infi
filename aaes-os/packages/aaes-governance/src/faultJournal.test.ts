import { describe, expect, it } from 'vitest';

import { asInvariantId, asRunId, asSpanId } from '@aaes-os/runledger';

import { FAULT_CODE_INVARIANT_BREACH } from './faultCodes.js';
import { FaultJournal } from './faultJournal.js';

describe('FaultJournal', () => {
  it('records faults with recurrence counting', () => {
    const journal = new FaultJournal();
    const runId = asRunId('run-1');
    const spanId = asSpanId('span-1');
    const invariantId = asInvariantId('operator_fast_compose');

    const first = journal.recordFault({
      runId,
      spanId,
      invariantId,
      faultCode: FAULT_CODE_INVARIANT_BREACH,
      severity: 'ERROR',
      contextSnapshot: { stage: 'cortex_execute' },
    });

    const second = journal.recordFault({
      runId,
      spanId,
      invariantId,
      faultCode: FAULT_CODE_INVARIANT_BREACH,
      severity: 'ERROR',
      contextSnapshot: { stage: 'cortex_execute' },
    });

    expect(first.recurrenceCount).toBe(1);
    expect(second.recurrenceCount).toBe(2);
    expect(journal.countRecurrence(FAULT_CODE_INVARIANT_BREACH, invariantId)).toBe(2);
  });

  it('filters by run, span, and fault code', () => {
    const journal = new FaultJournal();
    const runA = asRunId('run-a');
    const runB = asRunId('run-b');
    const spanA = asSpanId('span-a');
    const spanB = asSpanId('span-b');

    journal.recordFault({
      runId: runA,
      spanId: spanA,
      faultCode: FAULT_CODE_INVARIANT_BREACH,
      severity: 'WARN',
      contextSnapshot: {},
    });
    journal.recordFault({
      runId: runB,
      spanId: spanB,
      faultCode: 'AUTHORITY_MISMATCH',
      severity: 'CRITICAL',
      contextSnapshot: {},
    });

    expect(journal.getAll()).toHaveLength(2);
    expect(journal.getByRun(runA)).toHaveLength(1);
    expect(journal.getBySpan(spanB)).toHaveLength(1);
    expect(journal.getByFaultCode(FAULT_CODE_INVARIANT_BREACH)).toHaveLength(1);
  });
});
