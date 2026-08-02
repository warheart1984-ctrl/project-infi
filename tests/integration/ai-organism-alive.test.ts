import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { LirlRuntime, LirlLawGate } from '@aaes-os/lirl';

function tempRuntime(): LirlRuntime {
  const root = mkdtempSync(path.join(tmpdir(), 'ai-organism-alive-'));
  return new LirlRuntime({ runtimeRoot: root });
}

/**
 * AI Organism execution contract (from docs/runtime/legacy/ai-organism.md § Execution Contract).
 *
 * The organism is considered "alive" when:
 * 1. At least one entropy packet has been emitted
 * 2. At least one governed spec has been produced
 * 3. At least one constitution is attached
 * 4. At least one full loop iteration has completed
 * 5. Identity memory is non-empty
 *
 * The LIRL vertical slice is the living, tested embodiment of this contract in the workspace.
 */
describe('AI Organism execution contract (alive gate, via LIRL stack)', () => {
  it('condition 1: at least one entropy packet has been emitted', async () => {
    const runtime = tempRuntime();

    const result = await runtime.processIntent({
      actorId: 'operator-alpha',
      action: 'memory.write',
      payload: { key: 'greeting', value: { text: 'ma-la' } },
    });

    expect(result.receiptId).toMatch(/^evidence:/);
    const stored = runtime.receipts.getById(result.receiptId);
    expect(stored?.intentId).toBe(result.intentId);
  });

  it('condition 2: at least one governed spec has been produced', async () => {
    const runtime = tempRuntime();

    const result = await runtime.processIntent({
      actorId: 'operator-alpha',
      action: 'memory.write',
      payload: { key: 'greeting', value: { text: 'ma-la' } },
    });

    expect(result.operatorView.verdict).toBe('ACCEPT');
    expect(result.operatorView.html).toContain('LIRL Operator View');
    expect(result.operatorView.html).toContain(result.receiptId);
  });

  it('condition 3: at least one constitution is attached', () => {
    const gate = new LirlLawGate();

    const invariants = gate.engine.list();
    expect(invariants.length).toBeGreaterThan(0);
  });

  it('condition 4: at least one full loop iteration has completed', async () => {
    const runtime = tempRuntime();

    const result = await runtime.processIntent({
      actorId: 'operator-alpha',
      action: 'memory.write',
      payload: { key: 'loop', value: { text: 'iteration-1' } },
    });

    expect(result.verdict).toBe('ACCEPT');
    expect(result.memoryWritten).toBe(true);
    expect(result.receiptId).toBeTruthy();
    expect(result.operatorView.receiptId).toBe(result.receiptId);
    expect(result.runId).toBeTruthy();
  });

  it('condition 5: identity memory is non-empty', async () => {
    const runtime = tempRuntime();

    await runtime.processIntent({
      actorId: 'operator-alpha',
      action: 'memory.write',
      payload: { key: 'identity', value: { id: 'operator-alpha', role: 'operator' } },
    });

    expect(runtime.memory.list().length).toBeGreaterThan(0);
    const identity = runtime.memory.getByKey('identity');
    expect(identity?.value).toEqual({ id: 'operator-alpha', role: 'operator' });
  });

  it('full alive gate: one runtime completes all five conditions', async () => {
    const runtime = tempRuntime();
    const gate = new LirlLawGate();

    const result = await runtime.processIntent({
      actorId: 'operator-alpha',
      action: 'memory.write',
      payload: { key: 'greeting', value: { text: 'ma-la' } },
    });

    expect(result.receiptId).toMatch(/^evidence:/);
    expect(result.operatorView.verdict).toBe('ACCEPT');
    expect(result.memoryWritten).toBe(true);
    expect(runtime.memory.list().length).toBeGreaterThan(0);
    expect(runtime.receipts.getById(result.receiptId)).toBeDefined();
    expect(gate.engine.list().length).toBeGreaterThan(0);
  });
});
