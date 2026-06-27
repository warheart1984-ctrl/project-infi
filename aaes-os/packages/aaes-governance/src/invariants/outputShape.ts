import { asInvariantId } from '@aaes-os/runledger';

import { type Invariant, type InvariantContext, type InvariantResult } from '../invariantEngine.js';

/** Fails whenever output is not a plain object. */
export class OutputShapeInvariant implements Invariant {
  readonly id = asInvariantId('INV_OUTPUT_SHAPE');
  readonly name = 'Output must be an object';
  readonly description = 'Ensures runtime output is always a structured object.';

  async evaluate(ctx: InvariantContext): Promise<InvariantResult> {
    const passed = typeof ctx.output === 'object' && ctx.output !== null && !Array.isArray(ctx.output);

    return {
      invariantId: this.id,
      passed,
      message: passed ? 'Output shape OK' : 'Output was not an object',
      details: { actualType: typeof ctx.output },
    };
  }
}
