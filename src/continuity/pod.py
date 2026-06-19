"""POD (point-of-decision) layer references for continuity substrate binding."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PODDecision:
    """A lived decision that must map to CCS and ContinuityTrace when it matters."""

    decision_id: str
    actor_id: str
    subject_ref: str
    law_surfaces: list[str] = field(default_factory=list)
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "actor_id": self.actor_id,
            "subject_ref": self.subject_ref,
            "law_surfaces": list(self.law_surfaces),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }
