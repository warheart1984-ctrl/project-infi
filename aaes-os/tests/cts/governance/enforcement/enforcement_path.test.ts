import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('Governance enforcement path', () => {
  it('pre-run fault blocks execution receipt', async () => {
    const runtime = createCrk1Runtime();
    const bad = await runtime.execute({ payload: {} });
    expect(bad.ok).toBe(false);
    expect(runtime.getLedger().getReceipt(bad.runId)).toBeUndefined();
  });

  it('valid run passes governance and records receipt', async () => {
    const runtime = createCrk1Runtime();
    const good = await runtime.execute({ payload: { valid: true } });
    expect(good.ok).toBe(true);
    expect(runtime.getLedger().getReceipt(good.runId)).toBeDefined();
  });
});
