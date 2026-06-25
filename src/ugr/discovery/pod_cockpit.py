"""Discovery Pod cockpit DTOs — ledger-truth view for operator UI."""

from __future__ import annotations

from typing import Any

from src.ugr.discovery.discovery_pod_ledger import DiscoveryPodLedger


def _normalize_arc_tier(value: Any) -> str | None:
    tier = str(value or "").strip()
    if not tier or tier.lower() == "none":
        return None
    return tier


def pod_row_to_cockpit_dto(pod_id: str, row: dict[str, Any]) -> dict[str, Any]:
    """Map one registry row to the canonical cockpit Pod shape."""
    return {
        "pod_id": pod_id,
        "display_name": str(row.get("display_name") or pod_id),
        "proven_count": int(row.get("proven_count") or 0),
        "total_reputation_awarded": float(row.get("total_reputation_awarded") or 0),
        "discovery_count": int(row.get("discovery_count") or 0),
        "arc_tier": _normalize_arc_tier(row.get("governance_arc_tier")),
        "pod_reward_multiplier": float(row.get("pod_reward_multiplier") or 1.0),
    }


def build_pods_cockpit_payload(*, ledger: DiscoveryPodLedger | None = None) -> dict[str, Any]:
    """Aggregate pods from DiscoveryPodLedger.build_registry() (live ledger truth)."""
    engine = ledger or DiscoveryPodLedger()
    registry = engine.build_registry()
    pods_map = registry.get("pods") or {}
    pods = [
        pod_row_to_cockpit_dto(pod_id, row)
        for pod_id, row in sorted(
            pods_map.items(),
            key=lambda item: int((item[1] or {}).get("pod_index") or 0),
        )
    ]
    return {
        "registry_version": registry.get("registry_version"),
        "ledger_path": registry.get("ledger_path"),
        "authority": registry.get("authority"),
        "pods": pods,
        "count": len(pods),
    }


def get_pod_cockpit_dto(pod_id: str, *, ledger: DiscoveryPodLedger | None = None) -> dict[str, Any] | None:
    """Return cockpit DTO for one pod, or None if unknown."""
    engine = ledger or DiscoveryPodLedger()
    registry = engine.build_registry()
    row = (registry.get("pods") or {}).get(pod_id)
    if not row:
        return None
    payload = pod_row_to_cockpit_dto(pod_id, row)
    payload["operator_id"] = row.get("operator_id")
    payload["label"] = row.get("label") or ""
    payload["status"] = row.get("status") or "active"
    payload["last_discovered_at_utc"] = row.get("last_discovered_at_utc")
    payload["last_proven_at_utc"] = row.get("last_proven_at_utc")
    return payload
