import { randomUUID } from 'node:crypto';

import type { ExecutionSpan, ExecutionTrace } from './types.js';

export class ExecutionSpanManager {
  private readonly spans = new Map<string, ExecutionSpan>();

  startSpan(input: {
    intent_version: number;
    authority_token_id: string;
    parent_span?: string | null;
  }): ExecutionSpan {
    const span: ExecutionSpan = {
      span_id: randomUUID(),
      parent_span: input.parent_span ?? null,
      intent_version: input.intent_version,
      authority_token_id: input.authority_token_id,
      start_time: Date.now(),
      state: 'active',
      trace: [],
    };
    this.spans.set(span.span_id, span);
    return span;
  }

  recordTrace(span_id: string, step: ExecutionTrace): ExecutionSpan {
    const span = this.spans.get(span_id);
    if (!span) throw new Error(`unknown span: ${span_id}`);
    if (span.state !== 'active') throw new Error(`span not active: ${span.state}`);
    if (!step.justification.trim()) {
      throw new Error('EXECUTION_UNGOVERNED: trace step requires justification');
    }
    if (
      step.references.intent_version !== span.intent_version ||
      step.references.authority_token_id !== span.authority_token_id
    ) {
      throw new Error('EXECUTION_UNGOVERNED: trace references mismatch span bindings');
    }
    const updated: ExecutionSpan = {
      ...span,
      trace: [...span.trace, step],
    };
    this.spans.set(span_id, updated);
    return updated;
  }

  complete(span_id: string): ExecutionSpan {
    return this._terminal(span_id, 'completed');
  }

  terminate(span_id: string): ExecutionSpan {
    return this._terminal(span_id, 'terminated');
  }

  fault(span_id: string): ExecutionSpan {
    return this._terminal(span_id, 'faulted');
  }

  get(span_id: string): ExecutionSpan | null {
    return this.spans.get(span_id) ?? null;
  }

  private _terminal(span_id: string, state: 'completed' | 'terminated' | 'faulted'): ExecutionSpan {
    const span = this.spans.get(span_id);
    if (!span) throw new Error(`unknown span: ${span_id}`);
    const updated: ExecutionSpan = { ...span, state };
    this.spans.set(span_id, updated);
    return updated;
  }
}
