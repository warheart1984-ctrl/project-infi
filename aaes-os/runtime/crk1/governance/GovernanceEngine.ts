import type { InvariantResult } from './types.js';
import type { RunContext } from '../types.js';
import { coreInvariants } from './invariants/index.js';
import type { Invariant } from './types.js';

export class GovernanceEngine {
  constructor(private readonly invariants: Invariant[] = coreInvariants) {}

  listInvariants(): Invariant[] {
    return [...this.invariants];
  }

  checkPreRun(ctx: RunContext): InvariantResult {
    return this.evaluate({ run: ctx }, ['INV.NO_EMPTY_PAYLOAD']);
  }

  checkPostRun(ctx: RunContext, result: unknown): InvariantResult {
    return this.evaluate({ run: ctx, result }, ['INV.MUST_EMIT_EXECUTE_SPAN']);
  }

  private evaluate(
    ctx: { run: RunContext; result?: unknown },
    ids: string[],
  ): InvariantResult {
    for (const invariant of this.invariants) {
      if (!ids.includes(invariant.id)) continue;
      const outcome = invariant.check(ctx);
      if (!outcome.ok) {
        return outcome;
      }
    }
    return { ok: true };
  }
}
