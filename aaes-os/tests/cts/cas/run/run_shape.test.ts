import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('CAS Run shape', () => {
  it('returns ok result with runId for valid payload', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: { task: 'ping' } });
    expect(result.ok).toBe(true);
    expect(result.runId).toBeTruthy();
    expect(result.result).toBeDefined();
  });
});
