import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('CAS Run lifecycle', () => {
  it('init → execute → finalize → receipt', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: { step: 1 } });
    expect(result.ok).toBe(true);

    const receipt = runtime.getLedger().getReceipt(result.runId);
    expect(receipt).toBeDefined();
    expect(receipt!.spans.map((s) => s.type)).toEqual(['init', 'execute', 'finalize']);
  });

  it('fault path on empty payload produces no receipt', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: {} });
    expect(result.ok).toBe(false);
    expect(runtime.getLedger().getReceipt(result.runId)).toBeUndefined();
    expect(runtime.getLedger().getFault(result.runId)).toBeDefined();
  });
});
