import type { InvariantId, RunId, SpanId } from '@aaes-os/runledger';

import { FaultJournal } from './faultJournal.js';
import type { GovernanceTraceBus } from './tracePort.js';

export interface InvariantContext {
  runId: RunId;
  spanId: SpanId;
  input?: unknown;
  output?: unknown;
  metadata?: Record<string, unknown>;
}

export interface InvariantResult {
  invariantId: InvariantId;
  passed: boolean;
  message?: string;
  details?: unknown;
}

export interface Invariant {
  id: InvariantId;
  name: string;
  description: string;
  evaluate(ctx: InvariantContext): Promise<InvariantResult>;
}

/** InvariantEngine v0.1 — evaluates invariants and records faults. */
export class InvariantEngine {
  private readonly invariants: Invariant[] = [];

  constructor(
    private readonly faultJournal: FaultJournal,
    private readonly traceBus?: GovernanceTraceBus,
  ) {}

  register(invariant: Invariant): void {
    this.invariants.push(invariant);
  }

  async evaluateAll(ctx: InvariantContext): Promise<InvariantResult[]> {
    const results: InvariantResult[] = [];

    for (const inv of this.invariants) {
      const result = await inv.evaluate(ctx);
      results.push(result);

      this.traceBus?.emit({
        type: 'TRACE_INVARIANT',
        timestamp: new Date().toISOString(),
        runId: ctx.runId,
        spanId: ctx.spanId,
        invariantId: inv.id,
        passed: result.passed,
        message: result.message,
      });

      if (!result.passed) {
        const fault = this.faultJournal.recordFault({
          runId: ctx.runId,
          spanId: ctx.spanId,
          invariantId: inv.id,
          faultCode: `INV_FAIL_${inv.id}`,
          severity: 'ERROR',
          contextSnapshot: {
            message: result.message,
            details: result.details,
            input: ctx.input,
            output: ctx.output,
          },
        });

        this.traceBus?.emit({
          type: 'TRACE_FAULT',
          timestamp: fault.timestamp,
          runId: fault.runId,
          spanId: fault.spanId,
          fault,
        });
      }
    }

    return results;
  }
}
