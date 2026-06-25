import { describe, expect, it } from 'vitest';

import { validate } from '../../helpers/schemaValidator.js';

describe('CAS 1.0 JSON Schema — Run', () => {
  it('conforms to schema', () => {
    const run = {
      runId: 'run-1',
      identity: { id: 'agent-123', type: 'agent' },
      payload: { prompt: 'Hello' },
      createdAt: new Date().toISOString(),
    };

    expect(validate({ Run: run })).toBe(true);
  });

  it('rejects empty payload', () => {
    expect(
      validate({
        Run: {
          runId: 'run-1',
          identity: { id: 'agent-123', type: 'agent' },
          payload: {},
        },
      }),
    ).toBe(false);
  });
});
