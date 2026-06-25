import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('CTS noEmptyPayload', () => {
  it('blocks empty payloads', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: {} });
    expect(result.ok).toBe(false);
    expect(result.fault?.invariantId).toBe('INV.NO_EMPTY_PAYLOAD');
  });
});
