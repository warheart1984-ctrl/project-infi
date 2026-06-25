import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';

describe('CAS Fault shape', () => {
  it('fault has required fields on violation', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: {} });
    const fault = runtime.getLedger().getFault(result.runId)!;
    expect(fault.runId).toBe(result.runId);
    expect(fault.invariantId).toBeTruthy();
    expect(fault.message).toBeTruthy();
    expect(fault.timestamp).toBeTruthy();
  });
});
