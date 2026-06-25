import { describe, expect, it } from 'vitest';

import { RunStore } from '@aaes-os/runledger';

import {
  DeterminismInvariant,
  FaultJournal,
  InvariantEngine,
  OutputShapeInvariant,
  createMinimalInvariantEngine,
} from './index.js';

describe('OutputShapeInvariant', () => {
  it('fails on string output', async () => {
    const journal = new FaultJournal();
    const engine = new InvariantEngine(journal);
    engine.register(new OutputShapeInvariant());

    const store = new RunStore();
    const run = store.startRun();
    const span = store.startSpan(run.runId, { name: 'test' });

    const results = await engine.evaluateAll({
      runId: run.runId,
      spanId: span.spanId,
      input: {},
      output: 'not-an-object',
    });

    expect(results[0]?.passed).toBe(false);
    expect(journal.getByRun(run.runId)).toHaveLength(1);
    expect(journal.getByRun(run.runId)[0]?.faultCode).toBe('INV_FAIL_INV_OUTPUT_SHAPE');
  });
});

describe('DeterminismInvariant', () => {
  it('fails on output with random/timestamp fields', async () => {
    const journal = new FaultJournal();
    const engine = new InvariantEngine(journal);
    engine.register(new DeterminismInvariant());

    const store = new RunStore();
    const run = store.startRun();
    const span = store.startSpan(run.runId, { name: 'test' });

    await engine.evaluateAll({
      runId: run.runId,
      spanId: span.spanId,
      input: {},
      output: { rand: Math.random(), ts: Date.now() },
    });

    const faults = journal.getByRun(run.runId);
    expect(faults.length).toBeGreaterThanOrEqual(1);
    expect(faults.some((fault) => fault.invariantId === 'INV_DETERMINISM')).toBe(true);
  });
});

describe('InvariantEngine.evaluateAll', () => {
  it('records faults on every evaluation call', async () => {
    const { engine, journal } = createMinimalInvariantEngine();
    const store = new RunStore();
    const run = store.startRun();
    const span = store.startSpan(run.runId, { name: 'test' });

    const context = {
      runId: run.runId,
      spanId: span.spanId,
      input: {},
      output: 'bad',
    };

    await engine.evaluateAll(context);
    await engine.evaluateAll(context);

    expect(journal.getByRun(run.runId).length).toBeGreaterThanOrEqual(2);
  });
});
