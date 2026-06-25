import type { GovernanceEngine } from '../governance/GovernanceEngine.js';
import type { RunLedgerStore } from '../ledger/RunLedgerStore.js';
import type { TraceBus } from '../trace/TraceBus.js';
import type { RunContext, RunResult } from '../types.js';

interface LifecycleDeps {
  ctx: RunContext;
  governance: GovernanceEngine;
  ledger: RunLedgerStore;
  trace: TraceBus;
}

export async function runLifecycle(deps: LifecycleDeps): Promise<RunResult> {
  const { ctx, governance, ledger, trace } = deps;

  trace.emitSpan(ctx, 'init');

  const pre = governance.checkPreRun(ctx);
  if (!pre.ok) {
    await ledger.recordFault(ctx, pre);
    return {
      ok: false,
      runId: ctx.id,
      fault: {
        invariantId: pre.invariantId!,
        message: pre.message!,
      },
    };
  }

  trace.emitSpan(ctx, 'execute');
  const result = { echo: ctx.payload };

  const post = governance.checkPostRun(ctx, result);
  if (!post.ok) {
    await ledger.recordFault(ctx, post);
    return {
      ok: false,
      runId: ctx.id,
      fault: {
        invariantId: post.invariantId!,
        message: post.message!,
      },
    };
  }

  trace.emitSpan(ctx, 'finalize');
  await ledger.recordReceipt(ctx, result);

  return { ok: true, runId: ctx.id, result };
}
