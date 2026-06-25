import { SpanState, type GovernedSpan, type RuntimeContext } from "./types.js";

let spanCounter = 0;

export function createGovernedSpan(options?: {
  span_id?: string;
  parent_span_id?: string | null;
  runtime_context?: RuntimeContext | null;
}): GovernedSpan {
  const span_id = options?.span_id ?? `span_stub_${++spanCounter}`;
  const parent_span_id = options?.parent_span_id ?? null;
  let state: SpanState = SpanState.INIT;
  let runtime_context = options?.runtime_context ?? null;

  return {
    span_id,
    parent_span_id,
    get state() {
      return state;
    },
    set state(next: SpanState) {
      state = next;
    },
    get runtime_context() {
      return runtime_context;
    },
    set runtime_context(ctx: RuntimeContext | null) {
      runtime_context = ctx;
    },
    close() {
      if (state !== SpanState.RESULTED && state !== SpanState.CLOSED) {
        throw new Error(`AAES_SPAN_STATE_INVALID: cannot close span in state ${state}`);
      }
      state = SpanState.CLOSED;
    },
  };
}
