import { describe, expect, it } from 'vitest';

import { RunStore, asInvariantId } from './runStore.js';

describe('RunStore', () => {
  it('tracks run and span lifecycle', () => {
    const store = new RunStore();
    const run = store.startRun({ metadata: { label: 'demo' } });
    const span = store.startSpan(run.runId, { name: 'step-1' });

    store.linkInvariant(span.spanId, asInvariantId('operator_fast_compose'));
    store.endSpan(span.spanId);
    const ended = store.endRun(run.runId);

    expect(ended.endedAt).toBeDefined();
    expect(store.getInvariantLinks(span.spanId)).toHaveLength(1);
    expect(store.getSpan(span.spanId)?.endedAt).toBeDefined();
  });

  it('endSpan is idempotent', () => {
    const store = new RunStore();
    const run = store.startRun();
    const span = store.startSpan(run.runId, { name: 'step' });

    const first = store.endSpan(span.spanId);
    const second = store.endSpan(span.spanId);

    expect(second.endedAt).toBe(first.endedAt);
  });

  it('endRun is idempotent after first close', () => {
    const store = new RunStore();
    const run = store.startRun();
    const span = store.startSpan(run.runId, { name: 'step' });
    store.endSpan(span.spanId);

    const first = store.endRun(run.runId);
    const second = store.endRun(run.runId);

    expect(second.endedAt).toBe(first.endedAt);
  });

  it('linkInvariant deduplicates span/invariant pairs', () => {
    const store = new RunStore();
    const run = store.startRun();
    const span = store.startSpan(run.runId, { name: 'step' });
    const invariantId = asInvariantId('jarvis_authority');

    const first = store.linkInvariant(span.spanId, invariantId);
    const second = store.linkInvariant(span.spanId, invariantId);

    expect(second).toEqual(first);
    expect(store.getInvariantLinks(span.spanId)).toHaveLength(1);
  });

  it('rejects ending a run with open spans', () => {
    const store = new RunStore();
    const run = store.startRun();
    store.startSpan(run.runId, { name: 'open' });

    expect(() => store.endRun(run.runId)).toThrow(/open spans/i);
  });
});
