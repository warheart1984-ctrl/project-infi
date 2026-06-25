"""Tri-Strata governed memory types (Python mirror of TS types)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

IntentHorizon = Literal["short", "mid", "long"]
ExecutionSpanState = Literal["active", "completed", "terminated", "faulted"]
TraceStepType = Literal["reasoning", "tool_call", "observation", "decision"]
GovernedFaultCode = Literal[
    "INTENT_DRIFT",
    "AUTHORITY_INVALID",
    "AUTHORITY_REVOKED",
    "EXECUTION_UNGOVERNED",
    "MISSING_TRACE_JUSTIFICATION",
]


@dataclass(frozen=True)
class IntentRecord:
    intent_id: str
    timestamp: float
    operator_id: str
    semantic_goal: str
    constraints: tuple[str, ...]
    success_criteria: tuple[str, ...]
    horizon: IntentHorizon
    version: int
    signature: str
    content_hash: str
    prev_hash: str | None


@dataclass(frozen=True)
class AuthorityScope:
    resources: list[str]
    time_limit_ms: float
    intent_version: int


@dataclass
class AuthorityToken:
    token_id: str
    issued_by: str
    issued_to: str
    capabilities: list[str]
    scope: AuthorityScope
    delegation_chain: list[str] = field(default_factory=list)
    signature: str = ""
    revoked: bool = False


@dataclass(frozen=True)
class TraceReferences:
    intent_version: int
    authority_token_id: str


@dataclass(frozen=True)
class ExecutionTrace:
    timestamp: float
    step_type: TraceStepType
    content: str
    justification: str
    references: TraceReferences


@dataclass
class ExecutionSpan:
    span_id: str
    parent_span: str | None
    intent_version: int
    authority_token_id: str
    start_time: float
    state: ExecutionSpanState
    trace: list[ExecutionTrace] = field(default_factory=list)


@dataclass
class GovernanceViolation:
    code: str
    message: str
    span_id: str | None = None
    step_index: int | None = None


@dataclass
class ReplayResult:
    success: bool
    violations: list[GovernanceViolation] = field(default_factory=list)
    step_index: int | None = None
