import type { GovernedSpan, InvariantId, TraceEvent } from "./types.js";
import type { InvariantEngine } from "./types.js";
import { notImplemented } from "./error.js";

export class InvariantEngineStub implements InvariantEngine {
  check(_event: TraceEvent, _span: GovernedSpan, _prior: TraceEvent[]) {
    return notImplemented<void>("InvariantEngine.check");
  }

  check_ids(
    _ids: InvariantId[],
    _event: TraceEvent,
    _span: GovernedSpan,
    _prior: TraceEvent[],
  ) {
    return notImplemented<void>("InvariantEngine.check_ids");
  }
}
