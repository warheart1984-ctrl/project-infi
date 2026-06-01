"""Typed Jarvis <-> Nova interface scaffold for dormant Super Nova work."""

from __future__ import annotations

from dataclasses import dataclass, field


SUPER_NOVA_INTERFACE_VERSION = "jarvis_nova.interface.v1"


@dataclass(frozen=True, slots=True)
class ConstraintSet:
    """Shared bounded constraints for a Jarvis/Nova message."""

    time_budget: str | None = None
    scope: str | None = None
    sensitivity: str | None = None
    risk_level: str = "low"


@dataclass(frozen=True, slots=True)
class InterfaceEnvelope:
    """Versioned and traceable envelope for typed Jarvis/Nova exchange."""

    schema_version: str
    correlation_id: str
    source: str
    target: str
    payload_type: str


@dataclass(frozen=True, slots=True)
class ContextUpdate:
    """Jarvis -> Nova context surface without hidden execution authority."""

    task_id: str
    operator_focus: str
    environment_summary: str
    constraints: ConstraintSet = field(default_factory=ConstraintSet)


@dataclass(frozen=True, slots=True)
class ExecutionResultUpdate:
    """Jarvis -> Nova execution result summary."""

    task_id: str
    outcome: str
    summary: str
    notable_events: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OperatorSignal:
    """Jarvis -> Nova operator-visible approval or preference signal."""

    signal_type: str
    summary: str
    preference_hints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CognitiveSuggestion:
    """Nova -> Jarvis suggestion surface with no execution privilege."""

    suggestion_type: str
    task_id: str
    rationale: str
    constraints: ConstraintSet = field(default_factory=ConstraintSet)


@dataclass(frozen=True, slots=True)
class PlanDraft:
    """Nova -> Jarvis high-level plan draft that still requires Jarvis governance."""

    task_id: str
    steps: tuple[str, ...]
    assumptions: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExplanationRequest:
    """Nova -> Jarvis request for a structured explanation."""

    task_id: str
    target: str
    depth: str = "brief"


@dataclass(frozen=True, slots=True)
class PolicyViolationNotice:
    """Jarvis -> Nova violation response for rejected suggestions or plans."""

    task_id: str
    policy_id: str
    message: str


@dataclass(frozen=True, slots=True)
class ActivationHandshake:
    """Jarvis -> Super Nova handshake used by the dormant activation gate."""

    requested_stage: str = "super_nova"
    operator_intent: str = "explicit_super_nova_activation"
    continuity_mode: str = "session_continuity"
    anchor_source: str = "identity_anchor"
