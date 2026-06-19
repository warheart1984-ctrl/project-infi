import { describe, expect, it, vi } from 'vitest';

import { asRunId, asSpanId } from '@aaes-os/runledger';

import { TraceBusClient } from './bus.js';
import { consoleSink } from './console-sink.js';

describe('TraceBusClient', () => {
  it('delivers events to subscribers', () => {
    const bus = new TraceBusClient();
    const seen: string[] = [];
    bus.subscribe((event) => {
      seen.push(event.type);
    });

    bus.emit({
      type: 'TRACE_RUN',
      runId: asRunId('run-1'),
      timestamp: new Date().toISOString(),
      payload: { phase: 'started' },
    });

    expect(seen).toEqual(['TRACE_RUN']);
    expect(bus.getLog()).toHaveLength(1);
  });

  it('consoleSink logs without throwing', () => {
    const bus = new TraceBusClient();
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => undefined);
    bus.subscribe(consoleSink({ prefix: '[test]' }));

    bus.emit({
      type: 'TRACE_FAULT',
      runId: asRunId('run-2'),
      spanId: asSpanId('span-2'),
      timestamp: new Date().toISOString(),
      payload: { faultCode: 'INVARIANT_BREACH' },
    });

    expect(logSpy).toHaveBeenCalled();
    logSpy.mockRestore();
  });
});
