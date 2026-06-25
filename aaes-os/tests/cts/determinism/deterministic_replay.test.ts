import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../helpers/crk1Runtime.js';

describe('Deterministic replay', () => {
  it('repeated runs with fixed id produce identical receipt hashes', async () => {
    const payload = { replay: true };
    const id = 'replay-run-001';

    const r1 = createCrk1Runtime();
    const first = await r1.execute({ id, payload });
    const h1 = r1.getLedger().getReceipt(first.runId)!.hash;

    const r2 = createCrk1Runtime();
    const second = await r2.execute({ id, payload });
    const h2 = r2.getLedger().getReceipt(second.runId)!.hash;

    expect(h1).toBe(h2);
  });
});
