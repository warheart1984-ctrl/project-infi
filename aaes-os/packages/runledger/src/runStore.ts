import { randomUUID } from 'node:crypto';

import {
  asInvariantId,
  asRunId,
  asSpanId,
  type InvariantId,
  type InvariantLink,
  type RunId,
  type RunRecord,
  type SpanId,
  type SpanRecord,
} from './models.js';

export { asInvariantId } from './models.js';

export class RunLedgerError extends Error {
  constructor(
    readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = 'RunLedgerError';
  }
}

export interface StartRunOptions {
  runId?: RunId;
  metadata?: Record<string, unknown>;
}

export interface StartSpanOptions {
  spanId?: SpanId;
  name: string;
  parentSpanId?: SpanId;
  metadata?: Record<string, unknown>;
}

/** In-memory RunLedgerStore — run/span lifecycle and invariant linkage. */
export class RunStore {
  private readonly runs = new Map<RunId, RunRecord>();
  private readonly spans = new Map<SpanId, SpanRecord>();
  private readonly invariantLinks: InvariantLink[] = [];

  startRun(options: StartRunOptions = {}): RunRecord {
    const runId = options.runId ?? asRunId(randomUUID());
    if (this.runs.has(runId)) {
      throw new RunLedgerError('RUN_ALREADY_EXISTS', `run already exists: ${runId}`);
    }

    const record: RunRecord = {
      runId,
      startedAt: new Date().toISOString(),
      metadata: options.metadata,
    };
    this.runs.set(runId, record);
    return structuredClone(record);
  }

  endRun(runId: RunId): RunRecord {
    const run = this.requireRun(runId);
    if (run.endedAt) {
      return structuredClone(run);
    }

    const openSpans = this.getSpansByRun(runId).filter((span) => !span.endedAt);
    if (openSpans.length > 0) {
      throw new RunLedgerError(
        'OPEN_SPANS_REMAIN',
        `cannot end run with open spans: ${openSpans.map((s) => s.spanId).join(', ')}`,
      );
    }

    run.endedAt = new Date().toISOString();
    return structuredClone(run);
  }

  startSpan(runId: RunId, options: StartSpanOptions): SpanRecord {
    this.requireOpenRun(runId);

    const spanId = options.spanId ?? asSpanId(randomUUID());
    if (this.spans.has(spanId)) {
      throw new RunLedgerError('SPAN_ALREADY_EXISTS', `span already exists: ${spanId}`);
    }

    if (options.parentSpanId) {
      const parent = this.requireSpan(options.parentSpanId);
      if (parent.runId !== runId) {
        throw new RunLedgerError('SPAN_RUN_MISMATCH', 'parent span belongs to a different run');
      }
      if (parent.endedAt) {
        throw new RunLedgerError('PARENT_SPAN_CLOSED', 'parent span is already closed');
      }
    }

    const record: SpanRecord = {
      spanId,
      runId,
      name: options.name,
      startedAt: new Date().toISOString(),
      parentSpanId: options.parentSpanId,
      invariantIds: [],
    };
    this.spans.set(spanId, record);
    return structuredClone(record);
  }

  endSpan(spanId: SpanId): SpanRecord {
    const span = this.requireSpan(spanId);
    if (span.endedAt) {
      return structuredClone(span);
    }

    span.endedAt = new Date().toISOString();
    return structuredClone(span);
  }

  linkInvariant(spanId: SpanId, invariantId: InvariantId): InvariantLink {
    const span = this.requireSpan(spanId);
    const existing = this.invariantLinks.find(
      (link) => link.spanId === spanId && link.invariantId === invariantId,
    );
    if (existing) {
      return structuredClone(existing);
    }

    const link: InvariantLink = { spanId, invariantId };
    this.invariantLinks.push(link);
    span.invariantIds = [...(span.invariantIds ?? []), invariantId];
    return structuredClone(link);
  }

  getRun(runId: RunId): RunRecord | undefined {
    const run = this.runs.get(runId);
    return run ? structuredClone(run) : undefined;
  }

  getSpan(spanId: SpanId): SpanRecord | undefined {
    const span = this.spans.get(spanId);
    return span ? structuredClone(span) : undefined;
  }

  getSpansByRun(runId: RunId): SpanRecord[] {
    return [...this.spans.values()]
      .filter((span) => span.runId === runId)
      .map((span) => structuredClone(span));
  }

  getInvariantLinks(spanId?: SpanId): InvariantLink[] {
    if (spanId) {
      return this.invariantLinks
        .filter((link) => link.spanId === spanId)
        .map((link) => structuredClone(link));
    }
    return this.invariantLinks.map((link) => structuredClone(link));
  }

  private requireRun(runId: RunId): RunRecord {
    const run = this.runs.get(runId);
    if (!run) {
      throw new RunLedgerError('RUN_NOT_FOUND', `run not found: ${runId}`);
    }
    return run;
  }

  private requireOpenRun(runId: RunId): RunRecord {
    const run = this.requireRun(runId);
    if (run.endedAt) {
      throw new RunLedgerError('RUN_ALREADY_ENDED', `run already ended: ${runId}`);
    }
    return run;
  }

  private requireSpan(spanId: SpanId): SpanRecord {
    const span = this.spans.get(spanId);
    if (!span) {
      throw new RunLedgerError('SPAN_NOT_FOUND', `span not found: ${spanId}`);
    }
    return span;
  }
}
