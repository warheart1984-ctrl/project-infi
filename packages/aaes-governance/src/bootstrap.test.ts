import { describe, expect, it } from 'vitest';

import { initGovernanceGlobals, recordFaultWithPattern } from './bootstrap.js';
import { FAULT_CODE_INVARIANT_BREACH } from './faultCodes.js';
import { asRunId, asSpanId } from '@aaes-os/runledger';

describe('bootstrap', () => {
  it('initializes globals and ingests patterns on recordFaultWithPattern', () => {
    const { journal, patterns } = initGovernanceGlobals();
    const beforeFaults = journal.getAll().length;

    recordFaultWithPattern({
      runId: asRunId('run-bootstrap'),
      spanId: asSpanId('span-bootstrap'),
      faultCode: FAULT_CODE_INVARIANT_BREACH,
      severity: 'ERROR',
    });

    expect(journal.getAll().length).toBe(beforeFaults + 1);
    expect(patterns.getAll().length).toBeGreaterThan(0);
    expect(globalThis.faultJournal).toBe(journal);
    expect(globalThis.patternLedger).toBe(patterns);
  });
});
