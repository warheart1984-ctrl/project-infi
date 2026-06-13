"""Governed acceleration entitlement grants."""

from __future__ import annotations

from typing import Any

from src.ugr.rewards.acceleration_policy import acceleration_tokens_enabled
from src.ugr.rewards.acceleration_store import AccelerationStore

FORGE_500X = "forge_500x"
POD_ACCELERATION = "pod_acceleration"


def grant_forge_500x_entitlement(
    operator_id: str,
    *,
    tenant_id: str,
    contribution_id: str,
    runtime_dir: str | None = None,
) -> dict[str, Any]:
    if not acceleration_tokens_enabled():
        return {"status": "disabled", "skipped": True, "entitlement": FORGE_500X}
    return AccelerationStore(runtime_dir=runtime_dir, tenant_id=tenant_id).grant(
        operator_id,
        FORGE_500X,
        contribution_id=contribution_id,
    )


def grant_pod_acceleration(
    operator_id: str,
    tenant_id: str,
    contribution_id: str,
    *,
    discovery_result: dict[str, Any] | None = None,
    runtime_dir: str | None = None,
) -> dict[str, Any]:
    if (discovery_result or {}).get("idempotent_rediscovery"):
        return {
            "status": "skipped",
            "skipped": True,
            "reason": "idempotent_rediscovery",
            "entitlement": POD_ACCELERATION,
        }
    if not acceleration_tokens_enabled():
        return {"status": "disabled", "skipped": True, "entitlement": POD_ACCELERATION}
    result = AccelerationStore(runtime_dir=runtime_dir, tenant_id=tenant_id).grant(
        operator_id,
        POD_ACCELERATION,
        contribution_id=contribution_id,
    )
    if result.get("status") == "granted":
        result["status"] = "ok"
    return result
