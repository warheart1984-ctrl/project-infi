"""Shared reasoning protocol types for Jarvis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ObjectiveKind = Literal[
    "answer_relational_question",
    "answer_general_question",
    "inspect_repo",
    "debug_failure",
    "run_otem",
    "propose_patch",
    "apply_patch",
    "continue_scene",
    "review_architecture",
    "handle_direct_challenge",
]

OBJECTIVE_KINDS: tuple[str, ...] = (
    "answer_relational_question",
    "answer_general_question",
    "inspect_repo",
    "debug_failure",
    "run_otem",
    "propose_patch",
    "apply_patch",
    "continue_scene",
    "review_architecture",
    "handle_direct_challenge",
)


@dataclass(slots=True)
class ReasoningFactor:
    name: str
    weight: float
    value: Any
    source: str
    confidence: float
    trust: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "weight": self.weight,
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
            "trust": self.trust,
        }


@dataclass(slots=True)
class ReasoningConstraint:
    name: str
    value: Any
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "reason": self.reason,
        }


@dataclass(slots=True)
class OutputContract:
    final_answer_only: bool = True
    allow_trace: bool = True
    direct_answer_first: bool = True
    voice: str = "jarvis"
    verbosity: str = "concise"
    proposal_only: bool = False
    include_repo_grounding: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "final_answer_only": self.final_answer_only,
            "allow_trace": self.allow_trace,
            "direct_answer_first": self.direct_answer_first,
            "voice": self.voice,
            "verbosity": self.verbosity,
            "proposal_only": self.proposal_only,
            "include_repo_grounding": self.include_repo_grounding,
        }
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload
