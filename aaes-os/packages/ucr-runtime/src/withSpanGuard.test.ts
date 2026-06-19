import { describe, expect, it, vi } from 'vitest';

import { RunStore } from '@aaes-os/runledger';
import { TraceBus } from '@aaes-os/trace-bus';

import { withSpanGuard } from './withSpanGuard.js';

describe('withSpanGuard', () => {
  it('ends span even when fn throws', async () => {
    const runStore = new RunStore();
    const traceBus = new TraceBus();
    const run = runStore.startRun();

    await expect(
      withSpanGuard(runStore, traceBus, run.runId, 'test-span', async () => {
        throw new Error('boom');
      }),
    ).rejects.toThrow('boom');

    const spans = runStore.getSpansByRun(run.runId);
    expect(spans).toHaveLength(1);
    expect(spans[0]?.endedAt).toBeDefined();
  });

  it('emits span start and end trace events', async () => {
    const runStore = new RunStore();
    const traceBus = new TraceBus();
    const run = runStore.startRun();
    const emitSpy = vi.spyOn(traceBus, 'emit');

    await withSpanGuard(runStore, traceBus, run.runId, 'governed', async () => 'ok');

    expect(emitSpy).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'TRACE_SPAN_START', name: 'governed' }),
    );
    expect(emitSpy).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'TRACE_SPAN_END', name: 'governed' }),
    );
  });
});
