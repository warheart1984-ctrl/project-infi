import { describe, expect, it } from 'vitest';

import { validateDeterministicReplay } from '../../tools/validateDeterministicReplay.js';

describe('deterministic replay', () => {
  it('produces identical receipt hashes for identical payloads', async () => {
    await expect(validateDeterministicReplay()).resolves.toBeUndefined();
  });
});
