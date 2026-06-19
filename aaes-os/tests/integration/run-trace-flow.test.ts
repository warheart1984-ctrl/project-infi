import { describe, expect, it, vi } from 'vitest';

import { RunStore, asInvariantId } from '@aaes-os/runledger';
import { TraceBusClient, consoleSink } from '@aaes-os/trace-bus';

describe('run → span → trace → end integration', () => {
  it('wires RunStore with TraceBusClient', () => {
    const store = new RunStore();
    const bus = new TraceBusClient();
    const types: string[] = [];

    bus.subscribe((event) => {
      types.push(event.type);
    });
    bus.subscribe(consoleSink({ prefix: '[integration]' }));

    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => undefined);

    const run = store.startRun({ metadata: { label: 'integration-run' } });
    bus.emit({
      type: 'TRACE_RUN',
      runId: run.runId,
      timestamp: run.startedAt,
      payload: { phase: 'started' },
    });

    const span = store.startSpan(run.runId, { name: 'work' });
    bus.emit({
      type: 'TRACE_SPAN',
      runId: run.runId,
      spanId: span.spanId,
      timestamp: span.startedAt,
      payload: { phase: 'started' },
    });

    store.linkInvariant(span.spanId, asInvariantId('jarvis_authority'));
    bus.emit({
      type: 'TRACE_INVARIANT',
      runId: run.runId,
      spanId: span.spanId,
      timestamp: new Date().toISOString(),
      payload: { invariantId: 'jarvis_authority', passed: true },
    });

    store.endSpan(span.spanId);
    bus.emit({
      type: 'TRACE_SPAN',
      runId: run.runId,
      spanId: span.spanId,
      timestamp: new Date().toISOString(),
      payload: { phase: 'ended' },
    });

    const ended = store.endRun(run.runId);
    bus.emit({
      type: 'TRACE_RUN',
      runId: run.runId,
      timestamp: ended.endedAt!,
      payload: { phase: 'ended' },
    });

    expect(ended.endedAt).toBeDefined();
    expect(types).toEqual(['TRACE_RUN', 'TRACE_SPAN', 'TRACE_INVARIANT', 'TRACE_SPAN', 'TRACE_RUN']);
    expect(bus.getLog()).toHaveLength(5);
    expect(logSpy).toHaveBeenCalled();

    logSpy.mockRestore();
  });
});
