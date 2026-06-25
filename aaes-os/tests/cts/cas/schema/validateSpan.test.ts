import { describe, expect, it } from 'vitest';

import { validate } from '../../helpers/schemaValidator.js';

describe('CAS 1.0 JSON Schema — Span', () => {
  it('conforms to schema', () => {
    const span = {
      id: 'span-1',
      runId: 'run-1',
      type: 'execute',
      timestamp: Math.floor(Date.now()),
    };

    expect(validate({ Span: span })).toBe(true);
  });

  it('rejects non-integer timestamp', () => {
    expect(
      validate({
        Span: {
          id: 'span-1',
          runId: 'run-1',
          type: 'execute',
          timestamp: 1.5,
        },
      }),
    ).toBe(false);
  });
});
