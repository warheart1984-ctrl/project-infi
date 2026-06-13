"""Cloud Forge acceleration entitlement overlay."""

from __future__ import annotations

from typing import Any

from src.ugr.rewards.acceleration_entitlement import FORGE_500X, POD_ACCELERATION
from src.ugr.rewards.acceleration_policy import acceleration_tokens_enabled
from src.ugr.rewards.acceleration_store import AccelerationStore

HIGH_RISK = {"high", "critical", "constitutional"}


def resolve_effective_acceleration(
    rail: str,
    *,
    operator_id: str,
    tenant_id: str,
    risk: str,
    runtime_dir: str | None = None,
) -> dict[str, Any]:
    """Resolve the governed acceleration multiplier for one Cloud Forge dispatch."""
    normalized_risk = str(risk or "").strip().lower()
    normalized_rail = str(rail or "").strip().upper()
    if not acceleration_tokens_enabled():
        return {
            "acceleration_multiplier": 1,
            "acceleration_allowed": False,
            "reason": "acceleration_tokens_disabled",
            "rail": normalized_rail,
        }
    if normalized_risk in HIGH_RISK:
        return {
            "acceleration_multiplier": 1,
            "acceleration_allowed": False,
            "reason": "risk_clamped",
            "rail": normalized_rail,
        }

    store = AccelerationStore(runtime_dir=runtime_dir, tenant_id=tenant_id)
    if store.has(operator_id, FORGE_500X):
        multiplier = 500
        reason = "forge_500x_entitlement"
    elif store.has(operator_id, POD_ACCELERATION):
        multiplier = 50
        reason = "pod_acceleration_entitlement"
    else:
        multiplier = 1
        reason = "no_entitlement"

    return {
        "acceleration_multiplier": multiplier,
        "acceleration_allowed": multiplier > 1,
        "reason": reason,
        "rail": normalized_rail,
        "operator_id": operator_id,
        "tenant_id": tenant_id,
    }
