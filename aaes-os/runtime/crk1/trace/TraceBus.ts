import { randomUUID } from 'node:crypto';

import type { RunContext, Span } from '../types.js';
import type { TraceSink } from './TraceSink.js';
import { ConsoleTraceSink } from './TraceSink.js';

export class TraceBus {
  private lastTimestamp = 0;

  constructor(private readonly sink: TraceSink = new ConsoleTraceSink()) {}

  emitSpan(ctx: RunContext, type: string, data?: Record<string, unknown>): Span {
    const timestamp = Math.max(Date.now(), this.lastTimestamp + 1);
    this.lastTimestamp = timestamp;

    const span: Span = {
      id: randomUUID(),
      runId: ctx.id,
      type,
      timestamp,
      data,
    };
    ctx.spans.push(span);
    this.sink.onSpan(ctx, type);
    return span;
  }
}
