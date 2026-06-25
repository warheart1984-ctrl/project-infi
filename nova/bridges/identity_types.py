"""Identity bridge types for steward HUD."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class IdentityEvent:
    epoch: int
    identity: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"epoch": self.epoch, "identity": dict(self.identity)}

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> IdentityEvent:
        return cls(
            epoch=int(row.get("epoch") or 0),
            identity=dict(row.get("identity") or {}),
        )


@dataclass(frozen=True, slots=True)
class IdentitySnapshot:
    epoch: int
    identity: dict[str, Any]
    drift_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "epoch": self.epoch,
            "identity": dict(self.identity),
            "drift_scores": dict(self.drift_scores),
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> IdentitySnapshot:
        return cls(
            epoch=int(row.get("epoch") or 0),
            identity=dict(row.get("identity") or {}),
            drift_scores=dict(row.get("drift_scores") or {}),
        )
