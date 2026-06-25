"""Orchestration admission records — interface aaes_os.interface.v1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from src.aaes_os.governed_span import GovernedSpan
from src.aaes_os.models import AuthEnvelope, RuntimeContext
from src.aaes_os.trace_bus import TraceBusValidator
from src.aaes_os.types import StepType


@dataclass(frozen=True, slots=True)
class AAESRequest:
    trace_id: str
    intent_payload: dict[str, Any]
    runtime_context: RuntimeContext
    auth: AuthEnvelope
    module_id: str | None = None
    parent_span_id: str | None = None


@dataclass(slots=True)
class AAESContext:
    request: AAESRequest
    span: GovernedSpan
    bus: TraceBusValidator
    steps_completed: list[StepType] = field(default_factory=list)


StepStatus = Literal["pending", "ok", "failed", "skipped"]


@dataclass(frozen=True, slots=True)
class AAESStep:
    step_type: StepType
    step_id: str
    input_hash: str
    output_hash: str | None
    status: StepStatus
    error: dict[str, str] | None = None


@dataclass(frozen=True, slots=True)
class AAESDecision:
    allowed: bool
    reason_code: str
    policy_hash: str
    governor_auth: AuthEnvelope
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AAESAction:
    action_id: str
    tool: str
    args: dict[str, Any]
    executor_auth: AuthEnvelope
    rollback_possible: bool = True
