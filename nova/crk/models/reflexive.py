from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ReflexiveHealth = Literal["good", "degraded", "unknown"]


@dataclass(frozen=True)
class ReflexiveEvaluationReport:
    reasoning_trace_present: bool
    assumptions_logged: bool
    uncertainty_tracked: bool
    self_critique_score: float
    reflexive_health: ReflexiveHealth
    intent_id: str = ""
    epoch_id: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "reasoning_trace_present": self.reasoning_trace_present,
            "assumptions_logged": self.assumptions_logged,
            "uncertainty_tracked": self.uncertainty_tracked,
            "self_critique_score": self.self_critique_score,
            "reflexive_health": self.reflexive_health,
            "intent_id": self.intent_id,
            "epoch_id": self.epoch_id,
        }


@dataclass
class ReflexiveEpochSummary:
    epoch_id: str
    eval_count: int = 0
    degraded_count: int = 0
    latest_health: ReflexiveHealth = "unknown"
    health_sequence: list[ReflexiveHealth] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "epoch_id": self.epoch_id,
            "eval_count": self.eval_count,
            "degraded_count": self.degraded_count,
            "latest_health": self.latest_health,
            "health_sequence": list(self.health_sequence),
        }
