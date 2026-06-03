"""Cost-aware routing — mission budget and organ cost contracts."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from src.ugr.mission.provider_organ import ProviderOrgan
from src.ugr.mission.tenant_manifold import TenantManifoldState, tenant_hard_ceil


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class MissionBudget:
    soft_ceil: float
    hard_ceil: float
    per_step_max: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "soft_ceil": self.soft_ceil,
            "hard_ceil": self.hard_ceil,
            "per_step_max": self.per_step_max,
        }


@dataclass(frozen=True)
class OrganCostContract:
    cost_per_call: float
    cost_per_token: float | None = None
    region_multiplier: dict[str, float] | None = None

    @classmethod
    def from_organ(cls, organ: ProviderOrgan) -> OrganCostContract:
        raw = dict(organ.cost_contract or {})
        if not raw:
            return cls(cost_per_call=float(organ.max_cost_units or 0))
        return cls(
            cost_per_call=float(raw.get("cost_per_call") or organ.max_cost_units or 0),
            cost_per_token=float(raw["cost_per_token"]) if raw.get("cost_per_token") is not None else None,
            region_multiplier=dict(raw.get("region_multiplier") or {}),
        )


def compute_budget_digest(budget: MissionBudget) -> str:
    return sha256(_stable_json(budget.to_dict()).encode("utf-8")).hexdigest()


def resolve_mission_budget(
    request: dict[str, Any],
    *,
    tenant_manifold: TenantManifoldState | None = None,
) -> MissionBudget:
    constraints = dict(request.get("constraints") or {})
    raw = dict(constraints.get("mission_budget") or {})
    legacy_max = float(constraints.get("max_total_cost_units") or 9999)
    hard = float(raw.get("hard_ceil") or legacy_max)
    soft = float(raw.get("soft_ceil") or hard)
    per_step = raw.get("per_step_max")
    per_step_max = float(per_step) if per_step is not None else None
    tenant_ceil = tenant_hard_ceil(tenant_manifold)
    if tenant_ceil is not None:
        hard = min(hard, tenant_ceil)
        soft = min(soft, tenant_ceil)
    return MissionBudget(soft_ceil=soft, hard_ceil=hard, per_step_max=per_step_max)


def estimate_step_cost(
    organ: ProviderOrgan,
    *,
    region_id: str,
    est_tokens: int = 512,
) -> float:
    contract = OrganCostContract.from_organ(organ)
    mult = 1.0
    if contract.region_multiplier and region_id:
        mult = float(contract.region_multiplier.get(region_id) or 1.0)
    token_cost = 0.0
    if contract.cost_per_token is not None:
        token_cost = float(contract.cost_per_token) * float(est_tokens)
    return (contract.cost_per_call + token_cost) * mult


def rank_admissible_organs(
    candidates: list[ProviderOrgan],
    *,
    region_id: str,
    remaining_hard: float,
    per_step_max: float | None,
    est_tokens: int = 512,
) -> list[tuple[ProviderOrgan, float, str]]:
    """Return sorted (organ, estimated_cost, match_reason) cheapest first."""
    scored: list[tuple[ProviderOrgan, float, str]] = []
    for organ in candidates:
        est = estimate_step_cost(organ, region_id=region_id, est_tokens=est_tokens)
        if est > remaining_hard:
            continue
        if per_step_max is not None and est > per_step_max:
            continue
        scored.append((organ, est, f"cost_ranked_{est:.4f}"))
    return scored


def sort_ranked_by_trust(
    ranked: list[tuple[ProviderOrgan, float, str]],
    *,
    tenant_id: str,
) -> list[tuple[ProviderOrgan, float, str]]:
    from src.ugr.mission.organ_trust import effective_trust

    return sorted(
        ranked,
        key=lambda item: (
            item[1],
            -effective_trust(item[0].trust_score, tenant_id, item[0].organ_id),
            item[0].max_cost_units,
        ),
    )


@dataclass
class BudgetLedger:
    """Tracks soft/hard remaining budget across mission steps."""

    budget: MissionBudget
    spent: float = 0.0
    soft_ceil_breached: bool = False

    @property
    def remaining_hard(self) -> float:
        return max(0.0, self.budget.hard_ceil - self.spent)

    @property
    def remaining_soft(self) -> float:
        return max(0.0, self.budget.soft_ceil - self.spent)

    def would_exceed_hard(self, delta: float) -> bool:
        return (self.spent + delta) > self.budget.hard_ceil

    def charge(self, amount: float) -> None:
        self.spent += max(0.0, float(amount))
        if self.spent > self.budget.soft_ceil:
            self.soft_ceil_breached = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "budget": self.budget.to_dict(),
            "spent": self.spent,
            "remaining_hard": self.remaining_hard,
            "remaining_soft": self.remaining_soft,
            "soft_ceil_breached": self.soft_ceil_breached,
        }
