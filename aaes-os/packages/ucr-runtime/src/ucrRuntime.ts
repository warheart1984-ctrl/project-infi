import type { RunId, SpanId } from '@aaes-os/runledger';
import { RunStore } from '@aaes-os/runledger';
import {
  FAULT_CODE_SPAN_ORPHAN,
  createMinimalInvariantEngine,
  initGovernanceGlobals,
  type FaultEvent,
  type FaultJournal,
  type GovernanceTraceBus,
  type GovernanceTraceEvent,
  type InvariantEngine,
} from '@aaes-os/aaes-governance';
import {
  applyDeployedOutputPatches,
  getPatchLedger,
  seedApprovedPatches,
} from '@aaes-os/tri-core-protocol';
import { TraceBus } from '@aaes-os/trace-bus';

import { withSpanGuard } from './withSpanGuard.js';

export interface RuntimeIntent {
  kind?: string;
  payload?: unknown;
  metadata?: Record<string, unknown>;
  runIndex?: number;
}

export interface RuntimeResult {
  runId: RunId;
  output: unknown;
  faults: FaultEvent[];
  status: 'completed' | 'failed';
  spanOrphan?: boolean;
}

export type DemoRunMode = 'good' | 'string' | 'random' | 'throw';

export interface UCRRuntimeOptions {
  runStore?: RunStore;
  traceBus?: TraceBus;
  faultJournal?: FaultJournal;
  invariantEngine?: InvariantEngine;
  enablePatches?: boolean;
  demoSchedule?: DemoRunMode[];
  outputMode?: DemoRunMode;
}

const SPAN_NAME = 'runtime-execution';

/** UCRRuntime v0.1 — governed run loop with optional constitutional patches. */
export class UCRRuntime {
  private readonly runStore: RunStore;
  private readonly traceBus: TraceBus;
  private readonly faultJournal: FaultJournal;
  private readonly invariantEngine: InvariantEngine;
  private readonly enablePatches: boolean;
  private readonly demoSchedule: DemoRunMode[];
  private runCounter = 0;

  constructor(options: UCRRuntimeOptions = {}) {
    const { journal: globalJournal } = initGovernanceGlobals();
    this.runStore = options.runStore ?? new RunStore();
    this.traceBus = options.traceBus ?? new TraceBus();
    const wired = createMinimalInvariantEngine(
      options.faultJournal ?? globalJournal,
      asGovernanceTraceBus(this.traceBus),
    );
    this.faultJournal = wired.journal;
    this.invariantEngine = options.invariantEngine ?? wired.engine;
    this.enablePatches = options.enablePatches ?? false;
    if (this.enablePatches && !getPatchLedger()) {
      seedApprovedPatches();
    }
    this.demoSchedule = options.demoSchedule ?? (options.outputMode ? [options.outputMode] : []);
  }

  getTraceBus(): TraceBus {
    return this.traceBus;
  }

  async run(intent: RuntimeIntent = {}): Promise<RuntimeResult> {
    const runIndex = intent.runIndex ?? this.runCounter;
    this.runCounter += 1;

    const run = this.runStore.startRun({
      metadata: { kind: intent.kind, ...intent.metadata },
    });
    this.traceBus.runStart(run.runId);

    let spanOrphan = false;
    let output: unknown;
    let executionError: Error | undefined;

    const execute = async (activeSpanId: SpanId): Promise<void> => {
      const raw = await this.executePlan(intent, runIndex);
      output = this.enablePatches ? applyDeployedOutputPatches(raw) : raw;
      await this.invariantEngine.evaluateAll({
        runId: run.runId,
        spanId: activeSpanId,
        input: intent.payload,
        output,
      });
    };

    if (this.enablePatches) {
      try {
        await withSpanGuard(this.runStore, this.traceBus, run.runId, SPAN_NAME, execute);
      } catch (error) {
        executionError = error instanceof Error ? error : new Error(String(error));
      }
    } else {
      const span = this.runStore.startSpan(run.runId, { name: SPAN_NAME });
      this.traceBus.spanStart(run.runId, span.spanId, SPAN_NAME);
      try {
        await execute(span.spanId);
        this.runStore.endSpan(span.spanId);
        this.traceBus.spanEnd(run.runId, span.spanId, SPAN_NAME);
      } catch (error) {
        spanOrphan = true;
        executionError = error instanceof Error ? error : new Error(String(error));
        this.faultJournal.recordFault({
          runId: run.runId,
          spanId: span.spanId,
          faultCode: FAULT_CODE_SPAN_ORPHAN,
          severity: 'ERROR',
          contextSnapshot: {
            reason: 'span_orphan',
            message: executionError.message,
          },
        });
      }
    }

    const faults = this.faultJournal.getByRun(run.runId);
    const status = faults.length > 0 || spanOrphan || executionError ? 'failed' : 'completed';

    if (!spanOrphan) {
      this.runStore.endRun(run.runId);
    }

    this.traceBus.runEnd(run.runId);

    return {
      runId: run.runId,
      output,
      faults,
      status,
      spanOrphan,
    };
  }

  private async executePlan(intent: RuntimeIntent, runIndex: number): Promise<unknown> {
    const mode = this.resolveMode(runIndex);

    switch (mode) {
      case 'string':
        return `bad-output-${runIndex}`;
      case 'random':
        return {
          echo: intent.payload,
          rand: Math.random(),
          ts: Date.now(),
        };
      case 'throw':
        throw new Error('demo throw');
      default:
        return { echo: intent.payload };
    }
  }

  private resolveMode(runIndex: number): DemoRunMode {
    if (this.demoSchedule.length > 0) {
      return this.demoSchedule[runIndex % this.demoSchedule.length] ?? 'good';
    }
    return 'good';
  }
}

/** Alias retained for integration tests and demos. */
export const DefaultUCRRuntime = UCRRuntime;

function asGovernanceTraceBus(traceBus: TraceBus): GovernanceTraceBus {
  return {
    emit(event: GovernanceTraceEvent): void {
      traceBus.emit(event);
    },
    subscribe(listener: (event: GovernanceTraceEvent) => void): () => void {
      return traceBus.subscribe((event) => {
        if ((event.type === 'TRACE_INVARIANT' || event.type === 'TRACE_FAULT') && event.spanId) {
          listener(event as GovernanceTraceEvent);
        }
      });
    },
  };
}
