import { describe, expect, it } from 'vitest';

import { asInvariantId, asRunId, asSpanId } from '@aaes-os/runledger';

import { DriftMetrics } from './driftMetrics.js';
import { PatternLedger } from './patternLedger.js';
import { FaultJournal } from './faultJournal.js';

describe('DriftMetrics', () => {
  const drift = new DriftMetrics();

  it('returns score 0 when there are no faults', () => {
    const score = drift.computeDrift([], []);
    expect(score.score).toBe(0);
    expect(score.totalFaults).toBe(0);
  });

  it('reaches max fault component at 20 faults', () => {
    const journal = new FaultJournal();
    const patterns = new PatternLedger();
    const runId = asRunId('run-drift');
    const spanId = asSpanId('span-drift');

    for (let i = 0; i < 20; i += 1) {
      const fault = journal.recordFault({
        runId,
        spanId,
        invariantId: asInvariantId('INV_OUTPUT_SHAPE'),
        faultCode: `INV_FAIL_INV_OUTPUT_SHAPE`,
        severity: 'ERROR',
      });
      patterns.ingestFault(fault);
    }

    const score = drift.computeDrift(journal.getAll(), patterns.getAll());
    expect(score.totalFaults).toBe(20);
    expect(score.score).toBeGreaterThanOrEqual(0.7);
  });
});
