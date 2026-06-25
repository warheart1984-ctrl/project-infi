import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('CTS mustEmitExecuteSpan', () => {
  it('successful run emits execute span', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: { ok: true } });
    expect(result.ok).toBe(true);
    const receipt = runtime.getLedger().getReceipt(result.runId)!;
    expect(receipt.spans.some((s) => s.type === 'execute')).toBe(true);
  });
});
