import { UCRRuntime } from '../../runtime/crk1/UCRRuntime.js';
import type { Identity, IdentityType, RunRequest } from '../../runtime/crk1/types.js';
import { runMinimalCDP1 } from '../../benchmarks/cdp1/runMinimalCDP1.js';

export interface LocalSdkOptions {
  runtime?: UCRRuntime;
}

/**
 * In-process SDK over CRK-1 reference runtime (no HTTP).
 * Use RuntimeClient + cas/* modules for remote deployments.
 */
export function createLocalSdk(options: LocalSdkOptions = {}) {
  const runtime = options.runtime ?? new UCRRuntime();

  const identity = {
    create(input: { type: IdentityType; metadata?: Record<string, unknown> }) {
      return {
        id: `identity-${input.type}-${Date.now()}`,
        type: input.type,
        metadata: input.metadata ?? {},
      } satisfies Identity;
    },
    fromEnv(): Identity {
      const type = process.env.AAES_IDENTITY_TYPE;
      return {
        id: process.env.AAES_IDENTITY_ID ?? 'local-agent',
        type:
          type === 'agent' || type === 'model' || type === 'operator'
            ? type
            : 'agent',
        metadata: {},
      };
    },
    validate(id: Identity): boolean {
      return (
        Boolean(id.id) &&
        ['agent', 'model', 'operator'].includes(id.type) &&
        typeof id.metadata === 'object'
      );
    },
  };

  const run = {
    async start(input: { identity: Identity; payload: Record<string, unknown> }) {
      return runtime.execute({ identity: input.identity, payload: input.payload });
    },
    async execute(input: { identity?: Identity; payload: Record<string, unknown> }) {
      return runtime.execute({
        identity: input.identity ?? identity.fromEnv(),
        payload: input.payload,
      } satisfies RunRequest);
    },
    fromReceipt(runId: string) {
      return runtime.getLedger().getReceipt(runId);
    },
    async replay(runId: string) {
      const receipt = runtime.getLedger().getReceipt(runId);
      if (!receipt) throw new Error(`No receipt for run ${runId}`);
      return runtime.execute({
        id: runId,
        payload: (receipt.result as { echo?: Record<string, unknown> })?.echo ?? {},
      });
    },
  };

  const spans = {
    list(runId: string) {
      return runtime.getLedger().getReceipt(runId)?.spans ?? [];
    },
    filter(runId: string, query: { type?: string }) {
      return spans.list(runId).filter((s) => !query.type || s.type === query.type);
    },
    timeline(runId: string) {
      return spans.list(runId).sort((a, b) => a.timestamp - b.timestamp);
    },
  };

  const receipts = {
    get(runId: string) {
      return runtime.getLedger().getReceipt(runId);
    },
    hash(runId: string) {
      return runtime.getLedger().getReceipt(runId)?.hash;
    },
    compare(hashA: string, hashB: string) {
      return hashA === hashB;
    },
    export(runId: string) {
      const receipt = receipts.get(runId);
      if (!receipt) throw new Error(`No receipt for run ${runId}`);
      return JSON.stringify(receipt, null, 2);
    },
  };

  const faults = {
    get(runId: string) {
      return runtime.getLedger().getFault(runId);
    },
    list() {
      return runtime.getLedger().listFaults();
    },
    explain(fault: { invariantId: string; message: string }) {
      return `Invariant ${fault.invariantId}: ${fault.message}`;
    },
  };

  const governance = {
    invariants() {
      return runtime.getGovernance().listInvariants();
    },
  };

  return {
    runtime,
    identity,
    run,
    spans,
    receipts,
    faults,
    governance,
    cdp1: { runMinimal: runMinimalCDP1 },
  };
}

export type LocalSdk = ReturnType<typeof createLocalSdk>;
