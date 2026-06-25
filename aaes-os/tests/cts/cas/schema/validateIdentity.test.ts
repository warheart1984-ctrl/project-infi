import { describe, expect, it } from 'vitest';

import { formatValidationErrors, validate } from '../../helpers/schemaValidator.js';

describe('CAS 1.0 JSON Schema — Identity', () => {
  it('conforms to schema', () => {
    const identity = {
      id: 'agent-123',
      type: 'agent',
      metadata: { version: 1 },
    };

    expect(validate({ Identity: identity })).toBe(true);
    expect(formatValidationErrors()).toBe('');
  });

  it('rejects missing id', () => {
    expect(
      validate({
        Identity: { type: 'agent', metadata: {} },
      }),
    ).toBe(false);
  });

  it('rejects invalid type', () => {
    expect(
      validate({
        Identity: { id: 'x', type: 'human' },
      }),
    ).toBe(false);
  });
});
