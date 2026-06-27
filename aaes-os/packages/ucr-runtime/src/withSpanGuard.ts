import type { RunId, RunStore, SpanId } from '@aaes-os/runledger';
import type { TraceBus } from '@aaes-os/trace-bus';

/** PATCH_SPAN_BOUNDARY_001 — guarantee span close on success or failure. */
export async function withSpanGuard<T>(
  runStore: RunStore,
  traceBus: TraceBus,
  runId: RunId,
  name: string,
  fn: (spanId: SpanId) => Promise<T>,
): Promise<T> {
  const span = runStore.startSpan(runId, { name });
  traceBus.spanStart(runId, span.spanId, name);
  try {
    return await fn(span.spanId);
  } finally {
    runStore.endSpan(span.spanId);
    traceBus.spanEnd(runId, span.spanId, name);
  }
}
