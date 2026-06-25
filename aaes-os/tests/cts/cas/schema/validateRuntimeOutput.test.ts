import { describe, expect, it } from 'vitest';

import { createCrk1Runtime } from '../../../helpers/crk1Runtime.js';
import { validateCasObject } from '../../helpers/schemaValidator.js';

describe('CAS 1.0 JSON Schema — CRK-1 runtime output', () => {
  it('receipt and spans from a successful run conform', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: { prompt: 'schema-check' } });
    expect(result.ok).toBe(true);

    const receipt = runtime.getLedger().getReceipt(result.runId)!;
    expect(validateCasObject('Receipt', receipt)).toBe(true);

    for (const span of receipt.spans) {
      expect(validateCasObject('Span', span)).toBe(true);
    }

    expect(validateCasObject('ExecuteResponse', result)).toBe(true);
  });

  it('fault from a failed run conforms', async () => {
    const runtime = createCrk1Runtime();
    const result = await runtime.execute({ payload: {} });
    expect(result.ok).toBe(false);

    const fault = runtime.getLedger().getFault(result.runId);
    expect(fault).toBeDefined();
    expect(validateCasObject('Fault', fault)).toBe(true);
    expect(validateCasObject('ExecuteResponse', result)).toBe(true);
  });
});
