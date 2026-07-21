import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { LirlRuntime } from './loop.js';

function tempRuntime(): LirlRuntime {
  const root = mkdtempSync(path.join(tmpdir(), 'lirl-test-'));
  return new LirlRuntime({ runtimeRoot: root });
}

describe('LIRL vertical slice', () => {
  it('accepts lawful memory.write: gate accept → memory row → receipt → operator view', async () => {
    const runtime = tempRuntime();

    const result = await runtime.processIntent({
      actorId: 'operator-alpha',
      action: 'memory.write',
      payload: { key: 'greeting', value: { text: 'ma-la' } },
    });

    expect(result.verdict).toBe('ACCEPT');
    expect(result.memoryWritten).toBe(true);
    expect(result.receiptId).toMatch(/^evidence:/);

    const memoryRow = runtime.memory.getByKey('greeting');
    expect(memoryRow).toBeDefined();
    expect(memoryRow?.receiptId).toBe(result.receiptId);
    expect(memoryRow?.value).toEqual({ text: 'ma-la' });

    const stored = runtime.receipts.getById(result.receiptId);
    expect(stored).toBeDefined();
    expect(stored?.verdict).toBe('ACCEPT');

    expect(result.operatorView.receiptId).toBe(result.receiptId);
    expect(result.operatorView.verdict).toBe('ACCEPT');
    expect(result.operatorView.html).toContain(result.receiptId);

    const html = readFileSync(runtime.operatorHtmlPath, 'utf8');
    expect(html).toContain(result.receiptId);
    expect(html).toContain('ACCEPT');
  });

  it('rejects unlawful intent: gate reject → no memory write → rejection receipt', async () => {
    const runtime = tempRuntime();

    const result = await runtime.processIntent({
      actorId: 'operator-alpha',
      action: 'unlawful.bypass',
      payload: { key: 'secret', value: 'should-not-persist' },
      forceBypass: true,
    });

    expect(result.verdict).toBe('REJECT');
    expect(result.memoryWritten).toBe(false);
    expect(result.reasons.length).toBeGreaterThan(0);
    expect(result.receiptId).toMatch(/^evidence:/);

    expect(runtime.memory.getByKey('secret')).toBeUndefined();
    expect(runtime.memory.list()).toHaveLength(0);

    const stored = runtime.receipts.getById(result.receiptId);
    expect(stored).toBeDefined();
    expect(stored?.verdict).toBe('REJECT');

    expect(result.operatorView.receiptId).toBe(result.receiptId);
    expect(result.operatorView.verdict).toBe('REJECT');
    expect(result.operatorView.html).toContain('REJECT');
  });

  it('rejects memory.write with missing key without writing memory', async () => {
    const runtime = tempRuntime();

    const result = await runtime.processIntent({
      actorId: 'operator-beta',
      action: 'memory.write',
      payload: { value: 'orphan' },
    });

    expect(result.verdict).toBe('REJECT');
    expect(runtime.memory.list()).toHaveLength(0);
  });
});
