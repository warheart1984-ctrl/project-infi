import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('CAS Span emission', () => {
  it('emits at least one execute span', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: { ping: true } });
    const receipt = runtime.getLedger().getReceipt(result.runId)!;
    expect(receipt.spans.some((s) => s.type === 'execute')).toBe(true);
  });

  it('timestamps are monotonic', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: { ping: true } });
    const receipt = runtime.getLedger().getReceipt(result.runId)!;
    const times = receipt.spans.map((s) => s.timestamp);
    for (let i = 1; i < times.length; i++) {
      expect(times[i]).toBeGreaterThanOrEqual(times[i - 1]!);
    }
  });
});
