import { describe, expect, it } from 'vitest';

import { asInvariantId, asRunId, asSpanId } from '@aaes-os/runledger';

import { TraceBus } from './traceBus.js';
import type { TraceFaultEvent } from './traceEvents.js';

describe('TraceBus', () => {
  it('delivers TRACE_FAULT to subscribers', () => {
    const bus = new TraceBus();
    const seen: TraceFaultEvent[] = [];

    bus.subscribe((event) => {
      if (event.type === 'TRACE_FAULT') {
        seen.push(event);
      }
    });

    const runId = asRunId('run-fault');
    const spanId = asSpanId('span-fault');

    bus.emit({
      type: 'TRACE_FAULT',
      timestamp: new Date().toISOString(),
      runId,
      spanId,
      fault: {
        faultId: 'fault-1',
        runId,
        spanId,
        invariantId: asInvariantId('INV_OUTPUT_SHAPE'),
        timestamp: new Date().toISOString(),
        faultCode: 'INV_FAIL_INV_OUTPUT_SHAPE',
        severity: 'ERROR',
        contextSnapshot: {},
        recurrenceCount: 1,
      },
    });

    expect(seen).toHaveLength(1);
    expect(seen[0]?.fault.faultCode).toBe('INV_FAIL_INV_OUTPUT_SHAPE');
  });
});
