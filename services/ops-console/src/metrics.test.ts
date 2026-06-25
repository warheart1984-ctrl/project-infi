import { describe, expect, it } from 'vitest';

import { DriftMetrics, FaultJournal, PatternLedger } from '@aaes-os/aaes-governance';
import { asInvariantId, asRunId, asSpanId } from '@aaes-os/runledger';

import { buildMetrics } from './metrics.js';

describe('buildMetrics', () => {
  it('emits Prometheus text with drift, fault counters, and pattern gauges', () => {
    const journal = new FaultJournal();
    const patterns = new PatternLedger();

    const fault = journal.recordFault({
      runId: asRunId('run-metrics-1'),
      spanId: asSpanId('span-metrics-1'),
      invariantId: asInvariantId('INV_OUTPUT_SHAPE'),
      faultCode: 'INV_FAIL_INV_OUTPUT_SHAPE',
      severity: 'ERROR',
    });
    patterns.ingestFault(fault);

    const body = buildMetrics(journal, patterns);
    const drift = new DriftMetrics().computeDrift(journal.getAll(), patterns.getAll());

    expect(body).toContain('# TYPE aaes_drift_score gauge');
    expect(body).toContain(`aaes_drift_score ${drift.score}`);
    expect(body).toContain('# TYPE aaes_fault_events_total counter');
    expect(body).toContain('aaes_fault_events_total{fault_code="INV_FAIL_INV_OUTPUT_SHAPE"} 1');
    expect(body).toContain('# TYPE aaes_fault_pattern_recurrence gauge');
    expect(body).toContain('aaes_fault_pattern_recurrence{pattern_id=');
    expect(body.endsWith('\n')).toBe(true);
  });
});
