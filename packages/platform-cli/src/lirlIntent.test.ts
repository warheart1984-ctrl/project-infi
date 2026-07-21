import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { runLirlIntentCli } from './lirlIntent.js';

describe('platform-cli lirl intent', () => {
  it('accepts lawful memory.write locally without platform-api', async () => {
    const runtimeRoot = mkdtempSync(path.join(tmpdir(), 'cli-lirl-'));
    const { result } = await runLirlIntentCli({
      actorId: 'operator-cli',
      action: 'memory.write',
      payload: { key: 'cli-greeting', value: { text: 'ma-la' } },
      runtimeRoot,
    });

    expect(result.verdict).toBe('ACCEPT');
    expect(result.memoryWritten).toBe(true);
    expect(result.receiptId).toMatch(/^evidence:/);
  });

  it('rejects unlawful bypass locally', async () => {
    const runtimeRoot = mkdtempSync(path.join(tmpdir(), 'cli-lirl-'));
    const { result } = await runLirlIntentCli({
      actorId: 'operator-cli',
      action: 'unlawful.bypass',
      payload: { key: 'secret', value: 'nope' },
      forceBypass: true,
      runtimeRoot,
    });

    expect(result.verdict).toBe('REJECT');
    expect(result.memoryWritten).toBe(false);
  });
});
