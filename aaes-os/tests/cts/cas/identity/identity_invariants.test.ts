import { describe, expect, it } from 'vitest';

import type { Identity } from '../../../../runtime/crk1/types.js';

describe('CAS Identity invariants', () => {
  it('type must be from allowed set', () => {
    const allowed = new Set(['agent', 'model', 'operator']);
    const id: Identity = { id: 'x', type: 'agent', metadata: {} };
    expect(allowed.has(id.type)).toBe(true);
  });
});
