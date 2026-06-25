import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('CAS Receipt shape', () => {
  it('receipt contains all spans and result', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: { x: 1 } });
    const receipt = runtime.getLedger().getReceipt(result.runId)!;
    expect(receipt.runId).toBe(result.runId);
    expect(receipt.hash).toMatch(/^[a-f0-9]{64}$/);
    expect(receipt.spans.length).toBeGreaterThanOrEqual(3);
    expect(receipt.result).toEqual(result.result);
  });
});
