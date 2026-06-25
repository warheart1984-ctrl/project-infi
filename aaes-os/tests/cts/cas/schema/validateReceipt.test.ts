import { describe, expect, it } from 'vitest';

import { validate } from '../../helpers/schemaValidator.js';

describe('CAS 1.0 JSON Schema — Receipt', () => {
  it('conforms to schema', () => {
    const receipt = {
      runId: 'run-1',
      hash: 'abc123',
      spans: [],
      result: { echo: 'Hello' },
    };

    expect(validate({ Receipt: receipt })).toBe(true);
  });

  it('rejects missing hash', () => {
    expect(
      validate({
        Receipt: {
          runId: 'run-1',
          spans: [],
          result: null,
        },
      }),
    ).toBe(false);
  });
});
