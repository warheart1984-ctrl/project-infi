"""Trace bus — validate invariants and append immutable log."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from src.aaes_os.errors import AaesOsValidationError
from src.aaes_os.governed_span import GovernedSpan
from src.aaes_os.models import TraceEvent
from src.aaes_os.types import (
    CAUSAL_ORDER,
    ROLE_ALLOWED_EVENTS,
    STATE_FOR_EVENT,
    EventType,
    SpanState,
)


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


class TraceBusValidator:
    """Validate governed span events and maintain an append-only log."""

    def __init__(self) -> None:
        self._log: list[TraceEvent] = []
        self._spans: dict[str, GovernedSpan] = {}

    @property
    def log(self) -> tuple[TraceEvent, ...]:
        return tuple(self._log)

    def register_span(self, span: GovernedSpan) -> None:
        if not isinstance(span, GovernedSpan):
            raise TypeError("span must be GovernedSpan")
        if span.span_id in self._spans and self._spans[span.span_id] is not span:
            raise AaesOsValidationError("AAES_IDENTITY_DRIFT", f"span already registered: {span.span_id}")
        self._spans[span.span_id] = span

    def get_span(self, span_id: str) -> GovernedSpan | None:
        return self._spans.get(span_id)

    def events_for_span(self, span_id: str) -> list[TraceEvent]:
        return [event for event in self._log if event.span_id == span_id]

    def validate_and_append(self, event: TraceEvent, span: GovernedSpan) -> TraceEvent:
        if not isinstance(event, TraceEvent):
            raise TypeError("event must be TraceEvent")
        if not isinstance(span, GovernedSpan):
            raise TypeError("span must be GovernedSpan")
        if event.span_id != span.span_id:
            raise AaesOsValidationError("AAES_SPAN_STATE_INVALID", "event.span_id does not match span")

        self._validate_auth(event)
        self._validate_runtime_context(event)
        self._validate_hash(event)
        self._validate_role(event)
        self._validate_span_transition(event, span)

        required_from, required_to = STATE_FOR_EVENT[event.event_type]
        if span.state != required_from:
            raise AaesOsValidationError(
                "AAES_SPAN_STATE_INVALID",
                f"span in {span.state.value}; expected {required_from.value} for {event.event_type.value}",
            )

        self._validate_parent(event)
        self._validate_causal_order(event)
        self._validate_identity_consistency(event, span)

        if event.event_type == EventType.EXECUTION:
            prior = self.events_for_span(span.span_id)
            if not any(row.event_type == EventType.DECISION for row in prior):
                raise AaesOsValidationError("AAES_CAUSAL_VIOLATION", "EXECUTION requires prior DECISION (INV-7)")

        span._transition(required_to)
        self._log.append(event)
        self._spans[span.span_id] = span
        return event

    def _validate_auth(self, event: TraceEvent) -> None:
        try:
            event.auth.validate()
        except ValueError as exc:
            raise AaesOsValidationError("AAES_AUTH_MISSING", str(exc)) from exc

    def _validate_runtime_context(self, event: TraceEvent) -> None:
        try:
            event.runtime_context.validate()
        except ValueError as exc:
            raise AaesOsValidationError("AAES_RUNTIME_CONTEXT_INVALID", str(exc)) from exc

    def _validate_hash(self, event: TraceEvent) -> None:
        digest = sha256(_stable_json(event.canonical_body()).encode("utf-8")).hexdigest()
        if event.event_hash != digest:
            raise AaesOsValidationError("AAES_HASH_MISMATCH", "event_hash does not match canonical body")

    def _validate_role(self, event: TraceEvent) -> None:
        allowed = ROLE_ALLOWED_EVENTS.get(event.auth.role, frozenset())
        if event.event_type not in allowed:
            raise AaesOsValidationError(
                "AAES_AUTH_ROLE_DENIED",
                f"role {event.auth.role.value} cannot emit {event.event_type.value}",
            )

    def _validate_span_transition(self, event: TraceEvent, span: GovernedSpan) -> None:
        if span.state == SpanState.CLOSED:
            raise AaesOsValidationError("AAES_SPAN_STATE_INVALID", "span is CLOSED")

    def _validate_parent(self, event: TraceEvent) -> None:
        if event.event_type == EventType.INTENT:
            return
        parent_id = str(event.parent_event_id or "").strip()
        if not parent_id:
            raise AaesOsValidationError("AAES_PARENT_MISSING", "parent_event_id required after INTENT")
        known = {row.event_id for row in self._log if row.span_id == event.span_id}
        if parent_id not in known:
            raise AaesOsValidationError("AAES_PARENT_MISSING", f"parent_event_id not in log: {parent_id}")

    def _validate_causal_order(self, event: TraceEvent) -> None:
        prior_types = [row.event_type for row in self._log if row.span_id == event.span_id]
        if event.event_type in prior_types:
            raise AaesOsValidationError(
                "AAES_CAUSAL_VIOLATION",
                f"duplicate {event.event_type.value} in span",
            )
        expected_index = CAUSAL_ORDER.index(event.event_type)
        if expected_index != len(prior_types):
            expected = CAUSAL_ORDER[len(prior_types)].value
            raise AaesOsValidationError(
                "AAES_CAUSAL_VIOLATION",
                f"expected {expected}; got {event.event_type.value}",
            )

    def _validate_identity_consistency(self, event: TraceEvent, span: GovernedSpan) -> None:
        if span.runtime_context is None:
            span.runtime_context = event.runtime_context
            return
        if span.runtime_context.as_dict() != event.runtime_context.as_dict():
            raise AaesOsValidationError("AAES_IDENTITY_DRIFT", "runtime_context mismatch within span (INV-5)")
