from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CockpitSummarySchema:
    boundary_detection: dict[str, Any]
    reference_integrity: dict[str, Any]
    identity_history: dict[str, Any]
    pit_evolution: dict[str, Any]
    reflexive_evaluation: dict[str, Any]
    perception_health: dict[str, Any]
    amendment_history: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_detection": self.boundary_detection,
            "reference_integrity": self.reference_integrity,
            "identity_history": self.identity_history,
            "pit_evolution": self.pit_evolution,
            "reflexive_evaluation": self.reflexive_evaluation,
            "perception_health": self.perception_health,
            "amendment_history": self.amendment_history,
        }
