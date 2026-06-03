"""Auto-assign provider organs by tier, cost, region, and rail."""

from __future__ import annotations

from typing import Any

from src.ugr.mission.cost_routing import (
    MissionBudget,
    estimate_step_cost,
    rank_admissible_organs,
    resolve_mission_budget,
)
from src.ugr.mission.organ_trust import effective_trust
from src.ugr.mission.provider_organ import ORGAN_STATUS_ADMITTED, ProviderOrgan, ProviderOrganRegistry
from src.ugr.mission.tenant_manifold import TenantManifoldState
from src.ugr.platform.tenant_registry import normalize_tenant_id


TIER_ORDER = ("tiny", "mid", "big")
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _ordinal_tier(ordinal: int, step_count: int) -> str:
    """Demo heuristic: step 1→tiny, 2→mid, 3+→big."""
    if step_count <= 1:
        return "mid"
    if ordinal <= 1:
        return "tiny"
    if ordinal == 2:
        return "mid"
    return "big"


def _in_boundary_set(
    boundary_tuples: set[tuple[str, str, str]] | None,
    *,
    region_id: str,
    provider: str,
    rail: str,
) -> bool:
    if not boundary_tuples:
        return True
    key = (str(region_id or "").strip(), str(provider or "local").strip(), str(rail or "NORMAL").upper())
    return key in boundary_tuples


def _organ_admissible(
    organ: ProviderOrgan,
    *,
    region_id: str,
    intent: str,
    rail: str,
    risk_ceiling: str,
    cost_remaining: float,
    boundary_tuples: set[tuple[str, str, str]] | None = None,
) -> tuple[bool, str]:
    rail_upper = str(rail or "NORMAL").upper()
    if not _in_boundary_set(boundary_tuples, region_id=region_id, provider=organ.provider, rail=rail_upper):
        return False, f"({region_id},{organ.provider},{rail_upper}) outside B_cloud"

    allowed_regions = list(organ.contract.get("allowed_regions") or [])
    if region_id and region_id not in allowed_regions:
        return False, f"region {region_id} not in {allowed_regions}"
    allowed_domains = [str(d).lower() for d in (organ.contract.get("allowed_domains") or [])]
    if intent and intent not in allowed_domains:
        return False, f"intent {intent} not in allowed_domains"
    admissible_rails = [str(r).upper() for r in (organ.contract.get("admissible_rails") or [])]
    if admissible_rails and rail_upper not in admissible_rails:
        return False, f"rail {rail_upper} not admissible"
    organ_risk = str(organ.contract.get("risk_ceiling") or "high").lower()
    if RISK_ORDER.get(organ_risk, 2) > RISK_ORDER.get(risk_ceiling, 2):
        return False, f"organ risk {organ_risk} > ceiling {risk_ceiling}"
    if organ.max_cost_units > cost_remaining:
        return False, f"cost {organ.max_cost_units} > remaining {cost_remaining}"
    return True, "ok"


def resolve_step_organ(
    step: dict[str, Any],
    *,
    ordinal: int,
    step_count: int,
    organ_registry: ProviderOrganRegistry,
    region_id: str,
    intent: str,
    rail: str = "NORMAL",
    constraints: dict[str, Any] | None = None,
    cost_spent: float = 0.0,
    boundary_tuples: set[tuple[str, str, str]] | None = None,
    mission_budget: MissionBudget | None = None,
    tenant_manifold: TenantManifoldState | None = None,
) -> tuple[ProviderOrgan | None, dict[str, Any]]:
    """
    Resolve organ for one step.

    Priority: explicit organ_id → tier → ordinal heuristic.
    """
    constraints = dict(constraints or {})
    budget = mission_budget or resolve_mission_budget(
        {"constraints": constraints},
        tenant_manifold=tenant_manifold,
    )
    cost_remaining = budget.hard_ceil - cost_spent
    risk_ceiling = str(constraints.get("risk_ceiling") or "high").lower()

    explicit_id = str(step.get("organ_id") or "").strip()
    if explicit_id:
        organ = organ_registry.get(explicit_id)
        if organ and not _in_boundary_set(
            boundary_tuples,
            region_id=region_id,
            provider=organ.provider,
            rail=str(rail or "NORMAL").upper(),
        ):
            return None, {
                "auto_assigned": False,
                "match_reason": "explicit_organ_outside_B_cloud",
                "organ_id": explicit_id,
            }
        return organ, {
            "auto_assigned": False,
            "match_reason": "explicit_organ_id",
            "organ_id": explicit_id,
            "tier": organ.tier if organ else None,
        }

    requested_tier = str(step.get("tier") or "").strip().lower()
    if not requested_tier:
        requested_tier = _ordinal_tier(ordinal, step_count)

    admissible: list[ProviderOrgan] = []
    for organ in organ_registry.routable_organs():
        if organ.tier != requested_tier:
            continue
        if organ.status != ORGAN_STATUS_ADMITTED:
            continue
        ok, _reason = _organ_admissible(
            organ,
            region_id=region_id,
            intent=intent,
            rail=rail,
            risk_ceiling=risk_ceiling,
            cost_remaining=cost_remaining,
            boundary_tuples=boundary_tuples,
        )
        if ok:
            admissible.append(organ)

    ranked = rank_admissible_organs(
        admissible,
        region_id=region_id,
        remaining_hard=cost_remaining,
        per_step_max=budget.per_step_max,
    )
    from src.ugr.mission.cost_routing import sort_ranked_by_trust

    tenant_norm = normalize_tenant_id(tenant_manifold.tenant_id if tenant_manifold else "global")
    ranked = sort_ranked_by_trust(ranked, tenant_id=tenant_norm)
    if not ranked:
        return None, {
            "auto_assigned": True,
            "match_reason": f"no_admissible_organ_for_tier_{requested_tier}",
            "requested_tier": requested_tier,
            "organ_id": None,
        }

    chosen, est_cost, match_reason = ranked[0]
    return chosen, {
        "auto_assigned": True,
        "match_reason": match_reason,
        "requested_tier": requested_tier,
        "organ_id": chosen.organ_id,
        "provider": chosen.provider,
        "estimated_cost": est_cost,
    }


def apply_auto_assignments_to_steps(
    request: dict[str, Any],
    decomposition: dict[str, Any],
    *,
    organ_registry: ProviderOrganRegistry,
    rail: str = "NORMAL",
    cost_spent: float = 0.0,
    boundary_tuples: set[tuple[str, str, str]] | None = None,
    mission_budget: MissionBudget | None = None,
    tenant_manifold: TenantManifoldState | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return updated steps and per-step match metadata."""
    intent = str(request.get("intent") or "governed_super_router_demo").strip().lower()
    region_id = str(request.get("region_id") or "").strip()
    constraints = dict(request.get("constraints") or {})
    raw_steps = list(request.get("steps") or [])
    step_count = len(raw_steps)
    updated_steps: list[dict[str, Any]] = []
    match_meta: list[dict[str, Any]] = []
    budget = mission_budget or resolve_mission_budget(request, tenant_manifold=tenant_manifold)
    running_cost = cost_spent

    for ordinal, raw in enumerate(raw_steps, start=1):
        step = dict(raw)
        organ, meta = resolve_step_organ(
            step,
            ordinal=ordinal,
            step_count=step_count,
            organ_registry=organ_registry,
            region_id=region_id,
            intent=intent,
            rail=rail,
            constraints=constraints,
            cost_spent=running_cost,
            boundary_tuples=boundary_tuples,
            mission_budget=budget,
            tenant_manifold=tenant_manifold,
        )
        meta["step_id"] = str(step.get("step_id") or f"step-{ordinal}")
        meta["ordinal"] = ordinal
        if organ:
            step["organ_id"] = organ.organ_id
            est = float(meta.get("estimated_cost") or estimate_step_cost(organ, region_id=region_id))
            running_cost += est
        match_meta.append(meta)
        updated_steps.append(step)

    return updated_steps, match_meta
