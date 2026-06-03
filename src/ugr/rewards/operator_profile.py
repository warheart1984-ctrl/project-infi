"""Operator reward profile — reputation, rail credits, adoption multipliers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OperatorProfile:
    operator_id: str
    tenant_id: str
    reputation_score: float = 0.0
    rail_credits: float = 0.0
    adoption_multipliers: dict[str, float] = field(default_factory=dict)
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_id": self.operator_id,
            "tenant_id": self.tenant_id,
            "reputation_score": self.reputation_score,
            "rail_credits": self.rail_credits,
            "adoption_multipliers": dict(self.adoption_multipliers),
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> OperatorProfile:
        raw = dict(data or {})
        multipliers = dict(raw.get("adoption_multipliers") or {})
        return cls(
            operator_id=str(raw.get("operator_id") or ""),
            tenant_id=str(raw.get("tenant_id") or ""),
            reputation_score=float(raw.get("reputation_score") or 0),
            rail_credits=float(raw.get("rail_credits") or 0),
            adoption_multipliers={str(k): float(v) for k, v in multipliers.items()},
            updated_at=float(raw.get("updated_at") or 0),
        )

    def apply_deltas(
        self,
        *,
        reputation: float = 0,
        rail_credits: float = 0,
        adoption_multiplier_delta: float = 0,
        subsystem_id: str = "",
        multiplier_cap: float = 3.0,
        issued_at: float,
    ) -> None:
        if reputation:
            self.reputation_score = max(0.0, self.reputation_score + reputation)
        if rail_credits:
            self.rail_credits = max(0.0, self.rail_credits + rail_credits)
        if adoption_multiplier_delta and subsystem_id:
            current = float(self.adoption_multipliers.get(subsystem_id) or 1.0)
            next_val = min(multiplier_cap, current + adoption_multiplier_delta)
            self.adoption_multipliers[subsystem_id] = next_val
        self.updated_at = issued_at
