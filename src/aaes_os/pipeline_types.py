"""Cognitive pipeline records for AAES-OS architecture layer."""

# Mythic: AAES-OS cognitive pipeline
# Engineering: AaesOsPipelineTypes
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class AAESStepType(str, Enum):
    PERCEPTION = "perception"
    DELIBERATION = "deliberation"
    PLANNING = "planning"
    ACTION = "action"
    EXPLAIN = "explain"


class PolicyVerdict(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"


@dataclass(frozen=True, slots=True)
class AAESRequest:
    """Inbound operator or agent request."""

    prompt: str
    actor_id: str
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None

    def validate(self) -> None:
        if not str(self.prompt or "").strip():
            raise ValueError("prompt is required")
        if not str(self.actor_id or "").strip():
            raise ValueError("actor_id is required")


@dataclass(slots=True)
class AAESContext:
    """Mutable execution context for one orchestrated request."""

    trace_id: str
    request: AAESRequest
    normalized_input: str = ""
    steps: list["AAESStep"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.trace_id or "").strip():
            raise ValueError("trace_id is required")
        self.request.validate()


@dataclass(frozen=True, slots=True)
class AAESStep:
    """One pipeline stage observation."""

    step_type: AAESStepType
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    step_id: str = ""

    def __post_init__(self) -> None:
        if not self.step_id:
            object.__setattr__(self, "step_id", f"step_{uuid4().hex}")
        if not str(self.summary or "").strip():
            raise ValueError("summary is required")


@dataclass(frozen=True, slots=True)
class AAESDecision:
    """Governor decision emitted before bounded execution."""

    verdict: PolicyVerdict
    reason: str
    policy_id: str = "default"
    payload: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not str(self.reason or "").strip():
            raise ValueError("reason is required")


@dataclass(frozen=True, slots=True)
class AAESAction:
    """Bounded execution descriptor for pluggable modules."""

    module_id: str
    operation: str
    args: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not str(self.module_id or "").strip():
            raise ValueError("module_id is required")
        if not str(self.operation or "").strip():
            raise ValueError("operation is required")


@dataclass(frozen=True, slots=True)
class AAESExecuteResult:
    """Orchestrator outcome for HTTP and tests."""

    trace_id: str
    span_id: str
    status: str
    steps: tuple[AAESStep, ...]
    decision: AAESDecision | None
    outcome: dict[str, Any]
    explanation: str = ""
    blocked: bool = False
    block_code: str | None = None
