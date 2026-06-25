import { asInvariantId } from '@aaes-os/runledger';

import { type Invariant, type InvariantContext, type InvariantResult } from '../invariantEngine.js';

function hasNondeterministicValue(value: unknown, key?: string): boolean {
  if (value === '<random>' || value === '<timestamp>') {
    return false;
  }
  if (key === 'rand' || key === 'random') {
    return true;
  }
  if (typeof value === 'number' && value > 1e12) {
    return true;
  }
  if (value !== null && typeof value === 'object') {
    if (Array.isArray(value)) {
      return value.some((entry) => hasNondeterministicValue(entry));
    }
    return Object.entries(value as Record<string, unknown>).some(([childKey, childValue]) =>
      hasNondeterministicValue(childValue, childKey),
    );
  }
  return false;
}

/** Fails when output contains randomness or timestamp-like values. */
export class DeterminismInvariant implements Invariant {
  readonly id = asInvariantId('INV_DETERMINISM');
  readonly name = 'Output must be deterministic';
  readonly description = 'Fails if output contains randomness or timestamps.';

  async evaluate(ctx: InvariantContext): Promise<InvariantResult> {
    const out = ctx.output;

    if (typeof out !== 'object' || out === null || Array.isArray(out)) {
      return {
        invariantId: this.id,
        passed: true,
        message: 'Skipped: non-object output',
      };
    }

    const passed = !hasNondeterministicValue(out);

    return {
      invariantId: this.id,
      passed,
      message: passed
        ? 'Deterministic output'
        : 'Detected randomness or timestamp in output',
      details: { serialized: JSON.stringify(out) },
    };
  }
}
