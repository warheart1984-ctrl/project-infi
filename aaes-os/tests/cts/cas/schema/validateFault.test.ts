import { describe, expect, it } from 'vitest';

import { validate } from '../../helpers/schemaValidator.js';

describe('CAS 1.0 JSON Schema — Fault', () => {
  it('conforms to schema', () => {
    const fault = {
      runId: 'run-1',
      invariantId: 'INV.NO_EMPTY_PAYLOAD',
      message: 'Payload empty',
      timestamp: new Date().toISOString(),
    };

    expect(validate({ Fault: fault })).toBe(true);
  });

  it('rejects missing invariantId', () => {
    expect(
      validate({
        Fault: {
          runId: 'run-1',
          message: 'Payload empty',
        },
      }),
    ).toBe(false);
  });
});
