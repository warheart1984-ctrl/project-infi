import type { TraceEvent, TraceSubscriber } from './types.js';

export interface ConsoleSinkOptions {
  prefix?: string;
  filter?: (event: TraceEvent) => boolean;
}

/** Console sink for local development and integration tests. */
export function consoleSink(options: ConsoleSinkOptions = {}): TraceSubscriber {
  const prefix = options.prefix ?? '[trace-bus]';
  return (event: TraceEvent) => {
    if (options.filter && !options.filter(event)) {
      return;
    }
    const line = `${prefix} ${event.type} run=${event.runId}${event.spanId ? ` span=${event.spanId}` : ''}`;
    console.log(line, event.payload ?? {});
  };
}
