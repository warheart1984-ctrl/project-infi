"""Phase Gate enforces Jarvis admission law: existence is not activation, validation is not admission, and no component enters live operation without explicit phase approval."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
from enum import Enum
from threading import RLock
from typing import Any


class Phase(str, Enum):
    """Stable maturity phases for governed Jarvis components."""

    CONCEPT = "concept"
    PROTOTYPE = "prototype"
    VALIDATED = "validated"
    ACTIVE = "active"


PHASE_ORDER = {
    Phase.CONCEPT: 0,
    Phase.PROTOTYPE: 1,
    Phase.VALIDATED: 2,
    Phase.ACTIVE: 3,
}

KNOWN_CONTEXTS = {
    "live_runtime",
    "operator_runtime",
    "dreamspace_runtime",
    "sandbox",
    "test_harness",
    "development_only",
    "hidden_registry",
}

DEFAULT_ALLOWED_CONTEXTS = {
    Phase.CONCEPT: [],
    Phase.PROTOTYPE: ["sandbox", "test_harness"],
    Phase.VALIDATED: ["operator_runtime", "test_harness"],
    Phase.ACTIVE: ["live_runtime", "operator_runtime"],
}

PROTOTYPE_EXECUTION_CONTEXTS = {"sandbox", "test_harness", "development_only"}
VALIDATED_BLOCKED_EXECUTION_CONTEXTS = {"live_runtime", "hidden_registry"}
VALIDATED_BLOCKED_ROUTING_CONTEXTS = {"live_runtime", "hidden_registry"}


class PhaseGateError(Exception):
    """Base exception for phase gate failures."""


class ComponentNotRegisteredError(PhaseGateError):
    """Raised when a governed component is not registered."""


class PhaseViolationError(PhaseGateError):
    """Raised when a component is accessed outside its allowed phase or context."""


class IllegalPhaseTransitionError(PhaseGateError):
    """Raised when a promotion or demotion violates phase order."""


@dataclass(slots=True)
class PhaseHistoryEntry:
    """One explicit phase transition or registration event."""

    from_phase: str | None
    to_phase: str
    reason: str
    evidence: str | None = None
    actor: str | None = None
    recorded_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(slots=True)
class GovernedComponent:
    """One governed Jarvis component tracked by the phase gate."""

    component_id: str
    name: str
    component_type: str
    phase: Phase = Phase.CONCEPT
    allowed_contexts: list[str] = field(default_factory=list)
    notes: str | None = None
    validation_metadata: dict[str, Any] = field(default_factory=dict)
    history: list[PhaseHistoryEntry] = field(default_factory=list)


_REGISTRY: dict[str, GovernedComponent] = {}
_USES_DEFAULT_CONTEXT_POLICY: dict[str, bool] = {}
_PHASE_EVENTS: list[dict[str, Any]] = []
_LOCK = RLock()


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _normalize_component_id(value: Any) -> str:
    return _clean_text(value).lower().replace(" ", "_")


def _normalize_context(value: Any) -> str:
    return _clean_text(value).lower().replace("-", "_").replace(" ", "_")


def _normalize_contexts(values: list[str] | tuple[str, ...] | set[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in list(values or []):
        context = _normalize_context(value)
        if not context or context in seen:
            continue
        seen.add(context)
        normalized.append(context)
    return normalized


def _normalize_phase(value: Phase | str | None) -> Phase:
    if isinstance(value, Phase):
        return value
    normalized = _normalize_context(value or Phase.CONCEPT.value)
    try:
        return Phase(normalized)
    except ValueError as exc:
        raise IllegalPhaseTransitionError(f"Unknown phase '{value}'.") from exc


def _normalize_history_entry(entry: PhaseHistoryEntry) -> PhaseHistoryEntry:
    if not isinstance(entry, PhaseHistoryEntry):
        raise TypeError("History entries must be PhaseHistoryEntry instances.")
    return PhaseHistoryEntry(
        from_phase=_normalize_phase(entry.from_phase).value if entry.from_phase else None,
        to_phase=_normalize_phase(entry.to_phase).value,
        reason=_clean_text(entry.reason) or "Phase transition recorded.",
        evidence=_clean_text(entry.evidence) or None,
        actor=_clean_text(entry.actor) or None,
        recorded_at=_clean_text(entry.recorded_at) or datetime.now(UTC).isoformat(),
    )


def _clone_component(component: GovernedComponent) -> GovernedComponent:
    return deepcopy(component)


def _append_phase_event(event: str, **payload: Any) -> None:
    _PHASE_EVENTS.append(
        {
            "event": _normalize_context(event),
            "timestamp": datetime.now(UTC).isoformat(),
            **payload,
        }
    )


def _default_contexts_for_phase(phase: Phase) -> list[str]:
    return list(DEFAULT_ALLOWED_CONTEXTS.get(phase, []))


def _normalize_component(component: GovernedComponent) -> tuple[GovernedComponent, bool]:
    if not isinstance(component, GovernedComponent):
        raise TypeError("component must be a GovernedComponent.")

    component_id = _normalize_component_id(component.component_id)
    if not component_id:
        raise PhaseGateError("component_id is required.")

    phase = _normalize_phase(component.phase)
    allowed_contexts = _normalize_contexts(component.allowed_contexts)
    uses_default_context_policy = not allowed_contexts
    if uses_default_context_policy:
        allowed_contexts = _default_contexts_for_phase(phase)

    history = [_normalize_history_entry(entry) for entry in list(component.history or [])]
    if not history:
        history.append(
            PhaseHistoryEntry(
                from_phase=None,
                to_phase=phase.value,
                reason="Component registered in phase gate.",
            )
        )

    normalized_component = GovernedComponent(
        component_id=component_id,
        name=_clean_text(component.name) or component_id,
        component_type=_clean_text(component.component_type) or "component",
        phase=phase,
        allowed_contexts=allowed_contexts,
        notes=_clean_text(component.notes) or None,
        validation_metadata=deepcopy(dict(component.validation_metadata or {})),
        history=history,
    )
    return normalized_component, uses_default_context_policy


def _get_component_record(component_id: str) -> GovernedComponent:
    normalized_id = _normalize_component_id(component_id)
    component = _REGISTRY.get(normalized_id)
    if component is None:
        raise ComponentNotRegisteredError(f"Component '{component_id}' is not registered.")
    return component


def _contexts_label(component: GovernedComponent) -> str:
    if not component.allowed_contexts:
        return "no allowed contexts"
    return ", ".join(component.allowed_contexts)


def _execution_block_reason(component: GovernedComponent, context: str) -> str | None:
    if component.phase is Phase.CONCEPT:
        return (
            f"Component '{component.component_id}' is in concept phase and concept components are not executable."
        )
    if component.phase is Phase.PROTOTYPE and context not in PROTOTYPE_EXECUTION_CONTEXTS:
        return (
            f"Component '{component.component_id}' is in prototype phase and prototype components may run only in sandbox or test contexts."
        )
    if component.phase is Phase.VALIDATED and context in VALIDATED_BLOCKED_EXECUTION_CONTEXTS:
        return (
            f"Component '{component.component_id}' is in validated phase and validated components are not allowed in {context}."
        )
    if context not in component.allowed_contexts:
        return (
            f"Component '{component.component_id}' is not allowed in context '{context}'. Allowed contexts: {_contexts_label(component)}."
        )
    return None


def _routing_block_reason(component: GovernedComponent, context: str) -> str | None:
    if component.phase is Phase.CONCEPT:
        return (
            f"Component '{component.component_id}' is in concept phase and concept components are not routable."
        )
    if component.phase is Phase.PROTOTYPE:
        return (
            f"Component '{component.component_id}' is in prototype phase and prototype components are not routable."
        )
    if component.phase is Phase.VALIDATED and context in VALIDATED_BLOCKED_ROUTING_CONTEXTS:
        return (
            f"Component '{component.component_id}' is in validated phase and validated components are not routable in {context}."
        )
    if context not in component.allowed_contexts:
        return (
            f"Component '{component.component_id}' is not routable in context '{context}'. Allowed contexts: {_contexts_label(component)}."
        )
    return None


def _record_phase_block(component: GovernedComponent, *, context: str, reason: str, check: str) -> None:
    _append_phase_event(
        "phase_block",
        component_id=component.component_id,
        component_type=component.component_type,
        phase=component.phase.value,
        context=context,
        check=check,
        reason=reason,
    )


def reset_registry() -> None:
    """Clear the in-memory registry and audit state."""
    with _LOCK:
        _REGISTRY.clear()
        _USES_DEFAULT_CONTEXT_POLICY.clear()
        _PHASE_EVENTS.clear()


def list_phase_events(limit: int | None = None) -> list[dict[str, Any]]:
    """Return recent phase gate events in insertion order."""
    with _LOCK:
        events = list(_PHASE_EVENTS)
    if limit is None:
        return deepcopy(events)
    return deepcopy(events[-max(0, int(limit)):])


def register_component(component: GovernedComponent) -> None:
    """Register one governed component in the phase gate registry."""
    normalized_component, uses_default_context_policy = _normalize_component(component)
    with _LOCK:
        if normalized_component.component_id in _REGISTRY:
            raise PhaseGateError(
                f"Component '{normalized_component.component_id}' is already registered."
            )
        _REGISTRY[normalized_component.component_id] = normalized_component
        _USES_DEFAULT_CONTEXT_POLICY[normalized_component.component_id] = uses_default_context_policy
        _append_phase_event(
            "component_registered",
            component_id=normalized_component.component_id,
            component_type=normalized_component.component_type,
            phase=normalized_component.phase.value,
            allowed_contexts=list(normalized_component.allowed_contexts),
        )


def get_component(component_id: str) -> GovernedComponent:
    """Return one registered governed component."""
    with _LOCK:
        return _clone_component(_get_component_record(component_id))


def list_components() -> list[GovernedComponent]:
    """Return all registered governed components ordered by id."""
    with _LOCK:
        return [_clone_component(_REGISTRY[key]) for key in sorted(_REGISTRY)]


def can_promote_component(component_id: str, to_phase: Phase | str) -> bool:
    """Return whether a promotion path is legal for the component."""
    with _LOCK:
        component = _get_component_record(component_id)
        target_phase = _normalize_phase(to_phase)
    return PHASE_ORDER[target_phase] - PHASE_ORDER[component.phase] == 1


def can_demote_component(component_id: str, to_phase: Phase | str) -> bool:
    """Return whether a demotion path is legal for the component."""
    with _LOCK:
        component = _get_component_record(component_id)
        target_phase = _normalize_phase(to_phase)
    return PHASE_ORDER[target_phase] < PHASE_ORDER[component.phase]


def is_executable(component_id: str, context: str) -> bool:
    """Return whether the component may execute in the requested context."""
    normalized_context = _normalize_context(context)
    with _LOCK:
        component = _get_component_record(component_id)
        reason = _execution_block_reason(component, normalized_context)
    return reason is None


def assert_executable(component_id: str, context: str) -> None:
    """Fail closed when a component is executed outside its allowed phase or context."""
    normalized_context = _normalize_context(context)
    with _LOCK:
        component = _get_component_record(component_id)
        reason = _execution_block_reason(component, normalized_context)
        if reason is None:
            return
        _record_phase_block(component, context=normalized_context, reason=reason, check="execution")
    raise PhaseViolationError(reason)


def is_routable(component_id: str, context: str) -> bool:
    """Return whether routing may select the component in the requested context."""
    normalized_context = _normalize_context(context)
    with _LOCK:
        component = _get_component_record(component_id)
        reason = _routing_block_reason(component, normalized_context)
    return reason is None


def assert_routable(component_id: str, context: str) -> None:
    """Fail closed when routing would violate phase policy."""
    normalized_context = _normalize_context(context)
    with _LOCK:
        component = _get_component_record(component_id)
        reason = _routing_block_reason(component, normalized_context)
        if reason is None:
            return
        _record_phase_block(component, context=normalized_context, reason=reason, check="routing")
    raise PhaseViolationError(reason)


def promote_component(
    component_id: str,
    to_phase: Phase | str,
    reason: str,
    evidence: str | None = None,
    actor: str | None = None,
) -> None:
    """Promote one component exactly one legal phase forward."""
    target_phase = _normalize_phase(to_phase)
    with _LOCK:
        component = _get_component_record(component_id)
        if PHASE_ORDER[target_phase] - PHASE_ORDER[component.phase] != 1:
            raise IllegalPhaseTransitionError(
                f"Illegal promotion from {component.phase.value} to {target_phase.value}."
            )
        previous_phase = component.phase
        component.phase = target_phase
        if _USES_DEFAULT_CONTEXT_POLICY.get(component.component_id, False):
            component.allowed_contexts = _default_contexts_for_phase(target_phase)
        entry = PhaseHistoryEntry(
            from_phase=previous_phase.value,
            to_phase=target_phase.value,
            reason=_clean_text(reason) or "Phase promotion recorded.",
            evidence=_clean_text(evidence) or None,
            actor=_clean_text(actor) or None,
        )
        component.history.append(entry)
        _append_phase_event(
            "phase_promoted",
            component_id=component.component_id,
            component_type=component.component_type,
            from_phase=previous_phase.value,
            to_phase=target_phase.value,
            reason=entry.reason,
            evidence=entry.evidence,
            actor=entry.actor,
        )


def demote_component(
    component_id: str,
    to_phase: Phase | str,
    reason: str,
    evidence: str | None = None,
    actor: str | None = None,
) -> None:
    """Demote one component to a lower phase for rollback or containment."""
    target_phase = _normalize_phase(to_phase)
    with _LOCK:
        component = _get_component_record(component_id)
        if PHASE_ORDER[target_phase] >= PHASE_ORDER[component.phase]:
            raise IllegalPhaseTransitionError(
                f"Illegal demotion from {component.phase.value} to {target_phase.value}."
            )
        previous_phase = component.phase
        component.phase = target_phase
        if _USES_DEFAULT_CONTEXT_POLICY.get(component.component_id, False):
            component.allowed_contexts = _default_contexts_for_phase(target_phase)
        entry = PhaseHistoryEntry(
            from_phase=previous_phase.value,
            to_phase=target_phase.value,
            reason=_clean_text(reason) or "Phase demotion recorded.",
            evidence=_clean_text(evidence) or None,
            actor=_clean_text(actor) or None,
        )
        component.history.append(entry)
        _append_phase_event(
            "phase_demoted",
            component_id=component.component_id,
            component_type=component.component_type,
            from_phase=previous_phase.value,
            to_phase=target_phase.value,
            reason=entry.reason,
            evidence=entry.evidence,
            actor=entry.actor,
        )
