import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('CAS Fault emission', () => {
  it('emits fault on invariant violation', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: {} });
    expect(result.ok).toBe(false);
    expect(runtime.getLedger().getFault(result.runId)).toBeDefined();
  });

  it('fault does not produce a receipt', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: {} });
    expect(runtime.getLedger().getReceipt(result.runId)).toBeUndefined();
  });
});
