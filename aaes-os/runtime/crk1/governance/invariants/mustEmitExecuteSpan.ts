import type { Invariant } from '../types.js';

export const mustEmitExecuteSpan: Invariant = {
  id: 'INV.MUST_EMIT_EXECUTE_SPAN',
  description: 'Run must emit at least one execute span.',
  check(ctx) {
    const hasExecute = ctx.run.spans.some((span) => span.type === 'execute');
    if (!hasExecute) {
      return {
        ok: false,
        invariantId: 'INV.MUST_EMIT_EXECUTE_SPAN',
        message: 'No execute span emitted.',
      };
    }
    return { ok: true };
  },
};
