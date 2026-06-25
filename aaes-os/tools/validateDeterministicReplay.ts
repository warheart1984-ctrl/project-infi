import { strict as assert } from 'node:assert';

import {
  createTestRuntime,
  getDeterministicFingerprint,
} from '../tests/helpers/runtime.js';

async function runOnce(payload: Record<string, unknown>) {
  const { runtime, runStore } = createTestRuntime();
  const res = await runtime.run({ payload });
  if (res.status !== 'completed') {
    throw new Error('Run failed due to invariant violation or runtime fault.');
  }
  const hash = getDeterministicFingerprint(runStore, res.runId, res.output);
  return { res, hash };
}

export async function validateDeterministicReplay(): Promise<void> {
  const payload = { prompt: 'Determinism check.' };

  const r1 = await runOnce(payload);
  const r2 = await runOnce(payload);

  assert.equal(
    r1.hash,
    r2.hash,
    'Deterministic replay failed: receipt hashes differ.',
  );

  console.log('Deterministic replay validated. Hash:', r1.hash);
}

const isMain =
  typeof process.argv[1] === 'string' &&
  (process.argv[1].endsWith('validateDeterministicReplay.ts') ||
    process.argv[1].endsWith('validateDeterministicReplay.js'));

if (isMain) {
  validateDeterministicReplay().catch((err: unknown) => {
    console.error('Deterministic replay validation failed:', err);
    process.exit(1);
  });
}
