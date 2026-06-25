import { describe, expect, it } from 'vitest';

import type { Identity } from '../../../runtime/crk1/types.js';

function validIdentity(): Identity {
  return { id: 'agent-1', type: 'agent', metadata: { env: 'test' } };
}

describe('CAS Identity', () => {
  it('has required fields', () => {
    const id = validIdentity();
    expect(id.id).toBeTruthy();
    expect(['agent', 'model', 'operator']).toContain(id.type);
    expect(id.metadata).toBeTypeOf('object');
  });

  it('metadata is JSON-serializable', () => {
    const id = validIdentity();
    expect(() => JSON.stringify(id)).not.toThrow();
  });
});
