"""Constitutional IdentityObject — CRK-1 reference state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class IdentityObject:
    id: str
    mission: str
    values: tuple[str, ...]
    invariants: tuple[str, ...]
    authority_model: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "mission": self.mission,
            "values": list(self.values),
            "invariants": list(self.invariants),
            "authority_model": dict(self.authority_model),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> IdentityObject:
        return cls(
            id=str(payload["id"]),
            mission=str(payload["mission"]),
            values=tuple(str(v) for v in payload.get("values") or ()),
            invariants=tuple(str(v) for v in payload.get("invariants") or ()),
            authority_model=dict(payload.get("authority_model") or {}),
        )


DEFAULT_IDENTITY = IdentityObject(
    id="CIV-CORE-01",
    mission="Maintain a lawful, evidence-backed, steward-governable constitutional substrate.",
    values=("lawfulness", "comprehension", "meaning", "traceability"),
    invariants=(
        "No epoch commit without spine health.",
        "No decision without recoverable evidence.",
        "No execution without recorded outcome.",
    ),
    authority_model={
        "ROLE-STEWARD-01": {"approve": ["constitutional-change", "operational"]},
        "COUNCIL-01": {"approve": ["constitutional-change"]},
    },
)
