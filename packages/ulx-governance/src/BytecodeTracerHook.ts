import { randomUUID } from 'node:crypto';

import { TriCoreBus, type TriCoreMessage } from '@aaes-os/tri-core-protocol';

import type { ULXTrace } from './ULXTrace.js';

export interface BytecodeTracerHookOptions {
  bus?: TriCoreBus;
}

export class BytecodeTracerHook {
  constructor(private readonly options: BytecodeTracerHookOptions = {}) {}

  trace(source: string, bytecode: string, metadata: Record<string, unknown> = {}): ULXTrace {
    const trace: ULXTrace = {
      id: randomUUID(),
      source,
      bytecode,
      timestamp: Date.now(),
      verified: true,
      metadata,
    };

    const message: TriCoreMessage = {
      id: trace.id,
      from: 'runtime',
      to: 'governance',
      type: 'ULX_TRACE',
      payload: trace,
      timestamp: trace.timestamp,
      correlationId: trace.id,
    };

    void this.options.bus?.send(message);
    return trace;
  }
}
