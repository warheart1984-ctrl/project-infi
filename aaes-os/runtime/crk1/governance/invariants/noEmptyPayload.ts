import type { Invariant } from '../types.js';

export const noEmptyPayload: Invariant = {
  id: 'INV.NO_EMPTY_PAYLOAD',
  description: 'Run payload must not be empty.',
  check(ctx) {
    const payload = ctx.run.payload;
    if (!payload || Object.keys(payload).length === 0) {
      return {
        ok: false,
        invariantId: 'INV.NO_EMPTY_PAYLOAD',
        message: 'Run payload is empty.',
      };
    }
    return { ok: true };
  },
};
