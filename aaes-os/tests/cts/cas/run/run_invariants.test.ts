import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('CAS Run invariants', () => {
  it('rejects empty payload (INV.NO_EMPTY_PAYLOAD)', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: {} });
    expect(result.fault?.invariantId).toBe('INV.NO_EMPTY_PAYLOAD');
  });
});
