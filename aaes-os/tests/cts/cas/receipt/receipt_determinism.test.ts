import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('CAS Receipt determinism', () => {
  it('identical inputs produce identical receipt hashes', async () => {
    const payload = { prompt: 'determinism' };

    const r1 = createCrk1Runtime();
    const a = await r1.execute({ id: 'fixed-run-id', payload });
    const h1 = r1.getLedger().getReceipt(a.runId)!.hash;

    const r2 = createCrk1Runtime();
    const b = await r2.execute({ id: 'fixed-run-id', payload });
    const h2 = r2.getLedger().getReceipt(b.runId)!.hash;

    expect(h1).toBe(h2);
  });
});
