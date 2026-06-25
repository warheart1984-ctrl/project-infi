import { randomUUID } from 'node:crypto';

import { GovernanceEngine } from './governance/GovernanceEngine.js';
import type { RunLedgerStore } from './ledger/RunLedgerStore.js';
import { InMemoryRunLedgerStore } from './ledger/InMemoryRunLedgerStore.js';
import { runLifecycle } from './lifecycle/RunLifecycle.js';
import { TraceBus } from './trace/TraceBus.js';
import type { Identity, RunContext, RunRequest, RunResult } from './types.js';

export interface UCRRuntimeDeps {
  governance?: GovernanceEngine;
  ledger?: RunLedgerStore;
  trace?: TraceBus;
}

export class UCRRuntime {
  private readonly governance: GovernanceEngine;
  private readonly ledger: RunLedgerStore;
  private readonly trace: TraceBus;

  constructor(deps: UCRRuntimeDeps = {}) {
    this.governance = deps.governance ?? new GovernanceEngine();
    this.ledger = deps.ledger ?? new InMemoryRunLedgerStore();
    this.trace = deps.trace ?? new TraceBus();
  }

  getLedger(): RunLedgerStore {
    return this.ledger;
  }

  getGovernance(): GovernanceEngine {
    return this.governance;
  }

  getTraceBus(): TraceBus {
    return this.trace;
  }

  async execute(request: RunRequest): Promise<RunResult> {
    const runId = request.id ?? randomUUID();
    const identity: Identity = request.identity ?? {
      id: 'default-agent',
      type: 'agent',
      metadata: {},
    };

    const ctx: RunContext = {
      id: runId,
      identity,
      payload: request.payload,
      spans: [],
      createdAt: new Date().toISOString(),
    };

    return runLifecycle({
      ctx,
      governance: this.governance,
      ledger: this.ledger,
      trace: this.trace,
    });
  }
}
