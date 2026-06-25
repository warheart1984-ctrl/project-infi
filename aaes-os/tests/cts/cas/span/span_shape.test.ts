import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('CAS Span shape', () => {
  it('spans contain required fields', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: { a: 1 } });
    const receipt = runtime.getLedger().getReceipt(result.runId)!;
    for (const span of receipt.spans) {
      expect(span.id).toBeTruthy();
      expect(span.runId).toBe(result.runId);
      expect(span.type).toBeTruthy();
      expect(span.timestamp).toBeTypeOf('number');
    }
  });
});
