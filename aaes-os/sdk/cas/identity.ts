import { randomUUID } from 'node:crypto';

import type { Identity } from '../client/types.js';

export function createIdentity(params: {
  type: Identity['type'];
  metadata?: Record<string, unknown>;
}): Identity {
  return {
    id: randomUUID(),
    type: params.type,
    metadata: params.metadata ?? {},
  };
}

export function fromEnv(): Identity {
  const type = process.env.AAES_IDENTITY_TYPE;
  return {
    id: process.env.AAES_IDENTITY_ID ?? 'local-agent',
    type:
      type === 'agent' || type === 'model' || type === 'operator' ? type : 'agent',
    metadata: {},
  };
}

export function validateIdentity(identity: Identity): void {
  if (!identity.id) throw new Error('Identity.id is required');
  if (!['agent', 'model', 'operator'].includes(identity.type)) {
    throw new Error(`Invalid identity.type: ${identity.type}`);
  }
}
