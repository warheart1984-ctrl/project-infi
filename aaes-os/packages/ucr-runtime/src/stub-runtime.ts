import { randomUUID } from 'node:crypto';

import { RunStore } from '@aaes-os/runledger';
import { TraceBusClient } from '@aaes-os/trace-bus';

import type { UCRRunInput, UCRRunResult, UCRRuntime } from './types.js';

export interface StubUCRRuntimeOptions {
  runStore?: RunStore;
  traceBus?: TraceBusClient;
  spanName?: string;
}

/** Phase 3 stub — wires runledger + trace-bus for a minimal governed run. */
export class StubUCRRuntime implements UCRRuntime {
  private readonly runStore: RunStore;
  private readonly traceBus: TraceBusClient;
  private readonly spanName: string;

  constructor(options: StubUCRRuntimeOptions = {}) {
    this.runStore = options.runStore ?? new RunStore();
    this.traceBus = options.traceBus ?? new TraceBusClient();
    this.spanName = options.spanName ?? 'ucr.execute';
  }

  async run(input: UCRRunInput): Promise<UCRRunResult> {
    const run = this.runStore.startRun({ metadata: input.metadata });
    this.traceBus.emit({
      type: 'TRACE_RUN',
      runId: run.runId,
      timestamp: run.startedAt,
      payload: { label: input.label, ...input.payload },
    });

    const span = this.runStore.startSpan(run.runId, { name: this.spanName });
    this.traceBus.emit({
      type: 'TRACE_SPAN',
      runId: run.runId,
      spanId: span.spanId,
      timestamp: span.startedAt,
      payload: { name: span.name, phase: 'started' },
    });

    this.runStore.endSpan(span.spanId);
    this.traceBus.emit({
      type: 'TRACE_SPAN',
      runId: run.runId,
      spanId: span.spanId,
      timestamp: new Date().toISOString(),
      payload: { phase: 'ended' },
    });

    const ended = this.runStore.endRun(run.runId);
    this.traceBus.emit({
      type: 'TRACE_RUN',
      runId: run.runId,
      timestamp: ended.endedAt ?? new Date().toISOString(),
      payload: { phase: 'ended' },
    });

    return {
      runId: run.runId,
      status: 'completed',
      traceEventCount: this.traceBus.getLog().length,
    };
  }
}
