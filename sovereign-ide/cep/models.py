from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Invariant:
    invariant_id: str
    description: str
    check_fn: Callable[[dict[str, Any]], bool]


@dataclass
class InvariantSet:
    invariants: list[Invariant] = field(default_factory=list)

    def validate(self, agent_state: dict[str, Any]) -> bool:
        return all(invariant.check_fn(agent_state) for invariant in self.invariants)

    def list_ids(self) -> list[str]:
        return [invariant.invariant_id for invariant in self.invariants]


@dataclass(frozen=True)
class EvidenceItem:
    source: str
    payload: dict[str, Any]
    timestamp: int


@dataclass(frozen=True)
class LineageEvent:
    event_type: str
    payload: dict[str, Any]
    timestamp: int | None


@dataclass(frozen=True)
class DriftEnvelope:
    allowed_delta: float


@dataclass(frozen=True)
class AuditPacket:
    agent_id: str
    snapshot: dict[str, Any]
    conformance_status: bool
    timestamp: int


@dataclass(frozen=True)
class PromotionRequest:
    request_id: str
    agent_id: str
    snapshot: dict[str, Any]
    evidence_sample: list[dict[str, Any]]
    lineage_sample: list[dict[str, Any]]
    requested_change: dict[str, Any]


@dataclass(frozen=True)
class PromotionProposal:
    agent: Any
    payload: dict[str, Any]
    request: PromotionRequest


@dataclass(frozen=True)
class EvidenceResult:
    request_id: str
    passed: bool
    details: dict[str, Any]


@dataclass(frozen=True)
class LineageResult:
    request_id: str
    passed: bool
    details: dict[str, Any]


@dataclass(frozen=True)
class ReplayJob:
    request_id: str
    agent_id: str
    timeline_id: str
    window: dict[str, int]
    checks: list[str]


@dataclass(frozen=True)
class ReplayResult:
    request_id: str
    replay_id: str
    passed: bool
    violations: list[dict[str, Any]]


@dataclass(frozen=True)
class ConformanceResult:
    request_id: str
    passed: bool
    details: dict[str, Any]


@dataclass(frozen=True)
class PromotionDecision:
    decision_id: str
    request_id: str
    agent_id: str
    capability_id: str
    status: str
    timestamp: int
    evidence_ref: str
    lineage_ref: str
    replay_ref: str
    conformance_ref: str
