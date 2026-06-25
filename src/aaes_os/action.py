"""governed_action protocol helper."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from src.aaes_os.governed_span import GovernedSpan
from src.aaes_os.models import AuthEnvelope, RuntimeContext, TraceEvent
from src.aaes_os.trace_bus import TraceBusValidator
from src.aaes_os.types import EventType

T = TypeVar("T")


def governed_action(
    bus: TraceBusValidator,
    *,
    runtime_context: RuntimeContext,
    intent_auth: AuthEnvelope,
    intent_payload: dict[str, Any],
    decision_auth: AuthEnvelope,
    decision_payload: dict[str, Any],
    execution_auth: AuthEnvelope,
    execution_payload: dict[str, Any],
    execute_fn: Callable[[], T],
    result_auth: AuthEnvelope | None = None,
    span: GovernedSpan | None = None,
    parent_span_id: str | None = None,
) -> tuple[GovernedSpan, T, TraceEvent]:
    """Run INTENT → DECISION → EXECUTION → execute → RESULT → CLOSE."""
    if not isinstance(bus, TraceBusValidator):
        raise TypeError("bus must be TraceBusValidator")
    runtime_context.validate()
    intent_auth.validate()
    decision_auth.validate()
    execution_auth.validate()

    active_span = span or GovernedSpan(runtime_context=runtime_context, parent_span_id=parent_span_id)
    bus.register_span(active_span)

    intent_event = TraceEvent(
        span_id=active_span.span_id,
        event_type=EventType.INTENT,
        auth=intent_auth,
        runtime_context=runtime_context,
        payload=dict(intent_payload),
        parent_span_id=parent_span_id,
    )
    bus.validate_and_append(intent_event, active_span)

    decision_event = TraceEvent(
        span_id=active_span.span_id,
        event_type=EventType.DECISION,
        auth=decision_auth,
        runtime_context=runtime_context,
        payload=dict(decision_payload),
        parent_event_id=intent_event.event_id,
        parent_span_id=parent_span_id,
    )
    bus.validate_and_append(decision_event, active_span)

    execution_event = TraceEvent(
        span_id=active_span.span_id,
        event_type=EventType.EXECUTION,
        auth=execution_auth,
        runtime_context=runtime_context,
        payload=dict(execution_payload),
        parent_event_id=decision_event.event_id,
        parent_span_id=parent_span_id,
    )
    bus.validate_and_append(execution_event, active_span)

    outcome = execute_fn()

    result_role_auth = result_auth or execution_auth
    result_event = TraceEvent(
        span_id=active_span.span_id,
        event_type=EventType.RESULT,
        auth=result_role_auth,
        runtime_context=runtime_context,
        payload={"rollback_possible": True, "outcome": outcome},
        parent_event_id=execution_event.event_id,
        parent_span_id=parent_span_id,
    )
    bus.validate_and_append(result_event, active_span)
    active_span.close()
    return active_span, outcome, result_event
