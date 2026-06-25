import type { GovernedSpan, TraceBus, TraceEvent } from "./types.js";
import { err, notImplemented } from "./error.js";

export class TraceBusStub implements TraceBus {
  private readonly log: TraceEvent[] = [];
  private readonly spans = new Map<string, GovernedSpan>();

  validate(event: TraceEvent, span: GovernedSpan) {
    if (event.span_id !== span.span_id) {
      return err<TraceEvent>("AAES_SPAN_STATE_INVALID", "event.span_id does not match span");
    }
    return notImplemented<TraceEvent>("TraceBus.validate");
  }

  append(event: TraceEvent, span: GovernedSpan) {
    const validated = this.validate(event, span);
    if (!validated.ok) {
      return validated;
    }
    this.log.push(event);
    this.spans.set(span.span_id, span);
    return validated;
  }

  get_events(span_id: string): TraceEvent[] {
    return this.log.filter((event) => event.span_id === span_id);
  }

  validate_and_append(event: TraceEvent, span: GovernedSpan) {
    return this.append(event, span);
  }

  register_span(span: GovernedSpan): void {
    this.spans.set(span.span_id, span);
  }
}
