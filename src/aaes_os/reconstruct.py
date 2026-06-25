"""Deterministic span reconstruction."""

from __future__ import annotations

from src.aaes_os.errors import AaesOsValidationError
from src.aaes_os.models import ReconstructedSpan, RuntimeContext, TraceEvent
from src.aaes_os.trace_bus import TraceBusValidator
from src.aaes_os.types import CAUSAL_ORDER, EventType, SpanState


def reconstruct_span(bus: TraceBusValidator, span_id: str) -> ReconstructedSpan:
    if not isinstance(bus, TraceBusValidator):
        raise TypeError("bus must be TraceBusValidator")
    if not str(span_id or "").strip():
        raise ValueError("span_id is required")

    events = bus.events_for_span(span_id)
    if not events:
        raise AaesOsValidationError("AAES_RECONSTRUCT_FAILED", "no events for span")

    types = [event.event_type for event in events]
    if types != list(CAUSAL_ORDER[: len(types)]):
        raise AaesOsValidationError("AAES_RECONSTRUCT_FAILED", "causal chain incomplete or out of order")

    runtime_context: RuntimeContext | None = None
    for index, event in enumerate(events):
        if index > 0:
            parent_id = str(event.parent_event_id or "")
            if parent_id != events[index - 1].event_id:
                raise AaesOsValidationError("AAES_RECONSTRUCT_FAILED", "parent_event_id chain broken")
        if runtime_context is None:
            runtime_context = event.runtime_context
        elif runtime_context.as_dict() != event.runtime_context.as_dict():
            raise AaesOsValidationError("AAES_RECONSTRUCT_FAILED", "runtime_context drift")

    span = bus.get_span(span_id)
    state = span.state if span is not None else _infer_state(events)
    if runtime_context is None:
        raise AaesOsValidationError("AAES_RECONSTRUCT_FAILED", "missing runtime_context")

    return ReconstructedSpan(
        span_id=span_id,
        state=state,
        events=tuple(events),
        runtime_context=runtime_context,
    )


def _infer_state(events: list[TraceEvent]) -> SpanState:
    if not events:
        return SpanState.INIT
    last = events[-1].event_type
    mapping = {
        EventType.INTENT: SpanState.INTENTED,
        EventType.DECISION: SpanState.DECIDED,
        EventType.EXECUTION: SpanState.EXECUTING,
        EventType.RESULT: SpanState.RESULTED,
    }
    return mapping.get(last, SpanState.INIT)
