"""Operator reward profile — reputation, earned/purchased rail credits, adoption multipliers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OperatorProfile:
    operator_id: str
    tenant_id: str
    reputation_score: float = 0.0
    rail_credits: float = 0.0
    earned_rail_credits: float = 0.0
    purchased_rail_credits: float = 0.0
    adoption_multipliers: dict[str, float] = field(default_factory=dict)
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_id": self.operator_id,
            "tenant_id": self.tenant_id,
            "reputation_score": self.reputation_score,
            "rail_credits": self.rail_credits,
            "earned_rail_credits": self.earned_rail_credits,
            "purchased_rail_credits": self.purchased_rail_credits,
            "adoption_multipliers": dict(self.adoption_multipliers),
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> OperatorProfile:
        raw = dict(data or {})
        multipliers = dict(raw.get("adoption_multipliers") or {})
        earned = float(raw.get("earned_rail_credits") or raw.get("rail_credits") or 0)
        purchased = float(raw.get("purchased_rail_credits") or 0)
        total = float(raw.get("rail_credits") or (earned + purchased))
        return cls(
            operator_id=str(raw.get("operator_id") or ""),
            tenant_id=str(raw.get("tenant_id") or ""),
            reputation_score=float(raw.get("reputation_score") or 0),
            rail_credits=total,
            earned_rail_credits=earned,
            purchased_rail_credits=purchased,
            adoption_multipliers={str(k): float(v) for k, v in multipliers.items()},
            updated_at=float(raw.get("updated_at") or 0),
        )

    def _sync_total_credits(self) -> None:
        self.rail_credits = max(0.0, self.earned_rail_credits + self.purchased_rail_credits)

    def apply_deltas(
        self,
        *,
        reputation: float = 0,
        rail_credits: float = 0,
        earned_rail_credits: float = 0,
        purchased_rail_credits: float = 0,
        adoption_multiplier_delta: float = 0,
        contribution_id: str = "",
        subsystem_id: str = "",
        multiplier_cap: float = 3.0,
        issued_at: float,
    ) -> None:
        anchor = contribution_id or subsystem_id
        if reputation:
            self.reputation_score = max(0.0, self.reputation_score + reputation)
        if earned_rail_credits:
            self.earned_rail_credits = max(0.0, self.earned_rail_credits + earned_rail_credits)
        elif rail_credits:
            self.earned_rail_credits = max(0.0, self.earned_rail_credits + rail_credits)
        if purchased_rail_credits:
            self.purchased_rail_credits = max(0.0, self.purchased_rail_credits + purchased_rail_credits)
        self._sync_total_credits()
        if adoption_multiplier_delta and anchor:
            current = float(self.adoption_multipliers.get(anchor) or 1.0)
            next_val = min(multiplier_cap, current + adoption_multiplier_delta)
            self.adoption_multipliers[anchor] = next_val
        self.updated_at = issued_at

    def debit_credits(self, amount: float) -> dict[str, float]:
        """Debit purchased first (FIFO), then earned. Returns breakdown."""
        remaining = max(0.0, float(amount))
        from_purchased = min(self.purchased_rail_credits, remaining)
        self.purchased_rail_credits -= from_purchased
        remaining -= from_purchased
        from_earned = min(self.earned_rail_credits, remaining)
        self.earned_rail_credits -= from_earned
        self._sync_total_credits()
        return {"from_purchased": from_purchased, "from_earned": from_earned}
