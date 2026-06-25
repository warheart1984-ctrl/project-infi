import { describe, expect, it } from 'vitest';

import { FaultJournal, FAULT_CODE_INVARIANT_BREACH } from '@aaes-os/aaes-governance';
import { RunStore, asInvariantId } from '@aaes-os/runledger';
import { TraceBusClient } from '@aaes-os/trace-bus';

describe('v0.1 wire path', () => {
  it('runs startRun → startSpan → invariant fault → TRACE_FAULT → endSpan → endRun', () => {
    const runStore = new RunStore();
    const faultJournal = new FaultJournal();
    const traceBus = new TraceBusClient();

    const run = runStore.startRun();
    traceBus.emit({
      type: 'TRACE_RUN',
      runId: run.runId,
      timestamp: run.startedAt,
      payload: { phase: 'started' },
    });

    const span = runStore.startSpan(run.runId, { name: 'governed-step' });
    traceBus.emit({
      type: 'TRACE_SPAN',
      runId: run.runId,
      spanId: span.spanId,
      timestamp: span.startedAt,
      payload: { name: span.name, phase: 'started' },
    });

    const invariantId = asInvariantId('operator_fast_compose');
    runStore.linkInvariant(span.spanId, invariantId);

    const invariantFailed = true;
    let fault;
    if (invariantFailed) {
      fault = faultJournal.recordFault({
        runId: run.runId,
        spanId: span.spanId,
        invariantId,
        faultCode: FAULT_CODE_INVARIANT_BREACH,
        severity: 'ERROR',
        contextSnapshot: { reason: 'simulated invariant breach' },
      });

      traceBus.emit({
        type: 'TRACE_FAULT',
        runId: run.runId,
        spanId: span.spanId,
        timestamp: fault.timestamp,
        payload: fault,
      });
    }

    const endedSpan = runStore.endSpan(span.spanId);
    traceBus.emit({
      type: 'TRACE_SPAN',
      runId: run.runId,
      spanId: span.spanId,
      timestamp: endedSpan.endedAt!,
      payload: { phase: 'ended' },
    });

    const endedRun = runStore.endRun(run.runId);
    traceBus.emit({
      type: 'TRACE_RUN',
      runId: run.runId,
      timestamp: endedRun.endedAt!,
      payload: { phase: 'ended' },
    });

    expect(runStore.getRun(run.runId)?.endedAt).toBeDefined();
    expect(faultJournal.getByRun(run.runId)).toHaveLength(1);
    expect(fault?.faultCode).toBe(FAULT_CODE_INVARIANT_BREACH);

    const faultTraces = traceBus.getLog().filter((event) => event.type === 'TRACE_FAULT');
    expect(faultTraces).toHaveLength(1);
    expect(faultTraces[0]?.payload).toMatchObject({
      faultCode: FAULT_CODE_INVARIANT_BREACH,
      runId: run.runId,
      spanId: span.spanId,
    });
  });
});
