import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('Deterministic run', () => {
  it('same payload yields same result shape', async () => {
    const payload = { n: 42 };
    const r1 = createCrk1Runtime();
    const r2 = createCrk1Runtime();
    const a = await r1.execute({ payload });
    const b = await r2.execute({ payload });
    expect(a.result).toEqual(b.result);
  });
});
