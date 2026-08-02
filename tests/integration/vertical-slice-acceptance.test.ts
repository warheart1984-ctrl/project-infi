import { existsSync, readFileSync } from 'node:fs';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { LirlRuntime } from '@aaes-os/lirl';

const REPO_ROOT = path.resolve(process.cwd());

function tempRuntime(): LirlRuntime {
  const root = mkdtempSync(path.join(tmpdir(), 'vertical-slice-acceptance-'));
  return new LirlRuntime({ runtimeRoot: root });
}

const ACCEPTANCE_MODULES: Array<[string, string]> = [
  ['Intent API', 'packages/lirl/src/loop.ts'],
  ['Law gate', 'packages/lirl/src/lawGate.ts'],
  ['Memory write', 'packages/lirl/src/memory.ts'],
  ['Receipt', 'packages/lirl/src/receipts.ts'],
  ['Operator view', 'packages/lirl/src/operatorView.ts'],
  ['HTTP surface', 'services/platform-api/src/lirlRoutes.ts'],
];

describe('VERTICAL_SLICE.md acceptance criteria', () => {
  it('AC-1 happy path: accept → memory row → receipt id → operator view', async () => {
    const runtime = tempRuntime();

    const result = await runtime.processIntent({
      actorId: 'operator-alpha',
      action: 'memory.write',
      payload: { key: 'greeting', value: { text: 'ma-la' } },
    });

    expect(result.verdict).toBe('ACCEPT');

    const memoryRow = runtime.memory.getByKey('greeting');
    expect(memoryRow).toBeDefined();
    expect(memoryRow?.value).toEqual({ text: 'ma-la' });
    expect(memoryRow?.intentId).toBe(result.intentId);

    expect(result.receiptId).toMatch(/^evidence:/);
    expect(runtime.receipts.getById(result.receiptId)).toBeDefined();

    expect(result.operatorView.receiptId).toBe(result.receiptId);
    expect(result.operatorView.verdict).toBe('ACCEPT');
    expect(readFileSync(runtime.operatorHtmlPath, 'utf8')).toContain(result.receiptId);

    const persistedMemory = readFileSync(path.join(runtime.runtimeRoot, 'memory', 'memory.jsonl'), 'utf8');
    expect(persistedMemory).toContain(result.receiptId);
  });

  it('AC-2 reject path: unlawful → no memory → rejection receipt', async () => {
    const runtime = tempRuntime();

    const result = await runtime.processIntent({
      actorId: 'operator-alpha',
      action: 'unlawful.bypass',
      payload: { key: 'secret', value: 'should-not-persist' },
      forceBypass: true,
    });

    expect(result.verdict).toBe('REJECT');
    expect(result.reasons.length).toBeGreaterThan(0);
    expect(runtime.memory.list()).toHaveLength(0);

    expect(result.receiptId).toMatch(/^evidence:/);
    const stored = runtime.receipts.getById(result.receiptId);
    expect(stored?.verdict).toBe('REJECT');
    expect(stored?.memoryWritten).toBe(false);

    expect(result.operatorView.verdict).toBe('REJECT');
  });

  it('AC-3 docs list the exact implementation modules (all exist on disk)', () => {
    for (const [step, relativePath] of ACCEPTANCE_MODULES) {
      const absolute = path.join(REPO_ROOT, relativePath);
      expect(existsSync(absolute), `${step} module ${relativePath} must exist`).toBe(true);
    }

    const sliceDoc = readFileSync(path.join(REPO_ROOT, 'docs', 'civilization-os', 'VERTICAL_SLICE.md'), 'utf8');
    for (const [, relativePath] of ACCEPTANCE_MODULES) {
      expect(sliceDoc, `VERTICAL_SLICE.md must reference ${relativePath}`).toContain(relativePath);
    }
  });

  it('AC-4 scorecard notes the vertical slice', () => {
    const scorecard = readFileSync(path.join(REPO_ROOT, 'docs', 'scorecards', 'project-infi.md'), 'utf8');
    expect(scorecard).toContain('Vertical slice');
    expect(scorecard).toContain('LIRL');
  });
});
