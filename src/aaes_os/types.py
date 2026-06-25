"""AAES-OS v1.0 enumerations."""

from __future__ import annotations

from enum import Enum


class StepType(str, Enum):
    INGRESS = "INGRESS"
    INVARIANT_CHECK = "INVARIANT_CHECK"
    POLICY_EVAL = "POLICY_EVAL"
    MODULE_ROUTE = "MODULE_ROUTE"
    DECIDE = "DECIDE"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    EMIT_TRACE = "EMIT_TRACE"
    COMPLETE = "COMPLETE"


class InvariantId(str, Enum):
    SI_AUTHENTICITY = "SI_AUTHENTICITY"
    SI_TRACEABILITY = "SI_TRACEABILITY"
    SI_CAUSALITY = "SI_CAUSALITY"
    SI_RECONSTRUCTABILITY = "SI_RECONSTRUCTABILITY"
    SI_IDENTITY = "SI_IDENTITY"
    SI_REVERSIBILITY = "SI_REVERSIBILITY"
    SI_CONSTITUTION = "SI_CONSTITUTION"


class EventType(str, Enum):
    INTENT = "INTENT"
    DECISION = "DECISION"
    EXECUTION = "EXECUTION"
    RESULT = "RESULT"


class SpanState(str, Enum):
    INIT = "INIT"
    INTENTED = "INTENTED"
    DECIDED = "DECIDED"
    EXECUTING = "EXECUTING"
    RESULTED = "RESULTED"
    CLOSED = "CLOSED"


class Role(str, Enum):
    USER = "USER"
    RUNTIME = "RUNTIME"
    EXECUTOR = "EXECUTOR"
    GOVERNOR = "GOVERNOR"
    OBSERVER = "OBSERVER"


ROLE_ALLOWED_EVENTS: dict[Role, frozenset[EventType]] = {
    Role.USER: frozenset({EventType.INTENT}),
    Role.RUNTIME: frozenset({EventType.INTENT}),
    Role.GOVERNOR: frozenset({EventType.DECISION}),
    Role.EXECUTOR: frozenset({EventType.EXECUTION, EventType.RESULT}),
    Role.OBSERVER: frozenset(),
}

CAUSAL_ORDER: tuple[EventType, ...] = (
    EventType.INTENT,
    EventType.DECISION,
    EventType.EXECUTION,
    EventType.RESULT,
)

STATE_FOR_EVENT: dict[EventType, tuple[SpanState, SpanState]] = {
    EventType.INTENT: (SpanState.INIT, SpanState.INTENTED),
    EventType.DECISION: (SpanState.INTENTED, SpanState.DECIDED),
    EventType.EXECUTION: (SpanState.DECIDED, SpanState.EXECUTING),
    EventType.RESULT: (SpanState.EXECUTING, SpanState.RESULTED),
}
