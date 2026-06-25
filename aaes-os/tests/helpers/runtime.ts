import { createHash } from 'node:crypto';

import { createMinimalInvariantEngine } from '@aaes-os/aaes-governance';
import { RunStore, type RunId } from '@aaes-os/runledger';
import { UCRRuntime } from '@aaes-os/ucr-runtime';

export interface TestRuntimeBundle {
  runtime: UCRRuntime;
  runStore: RunStore;
}

/** Shared test harness for CTS, CDP-1, and determinism validators. */
export function createTestRuntime(): TestRuntimeBundle {
  const runStore = new RunStore();
  const { engine, journal } = createMinimalInvariantEngine();

  const runtime = new UCRRuntime({
    runStore,
    faultJournal: journal,
    invariantEngine: engine,
    demoSchedule: ['good'],
    enablePatches: false,
  });

  return { runtime, runStore };
}

/** Deterministic fingerprint — excludes runId, spanId, and timestamps. */
export function getDeterministicFingerprint(
  runStore: RunStore,
  runId: RunId,
  output: unknown,
): string {
  const spans = runStore.getSpansByRun(runId).map((span) => ({
    name: span.name,
    parentName: span.parentSpanId
      ? runStore.getSpan(span.parentSpanId)?.name
      : undefined,
    invariantIds: span.invariantIds ?? [],
  }));
  const payload = JSON.stringify({ output, spans });
  return createHash('sha256').update(payload).digest('hex');
}

/** Full ledger snapshot hash (includes ids and timestamps). */
export function getReceiptHash(runStore: RunStore, runId: RunId): string {
  const run = runStore.getRun(runId);
  if (!run) {
    throw new Error(`Run not found: ${runId}`);
  }
  const spans = runStore.getSpansByRun(runId);
  const links = spans.flatMap((span) => runStore.getInvariantLinks(span.spanId));
  const payload = JSON.stringify({ run, spans, links });
  return createHash('sha256').update(payload).digest('hex');
}
