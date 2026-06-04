"""Attribution chain and mandatory discovery receipt resolution."""

from __future__ import annotations

from hashlib import sha256
import json
import time
from typing import Any

from src.ugr.discovery.subsystem_discovery_receipt import verify_subsystem_discovery_receipt
from src.ugr.discovery.subsystem_discovery_store import SubsystemDiscoveryStore
from src.ugr.platform.tenant_registry import normalize_tenant_id
from src.ugr.rewards.operator_reward_spec import LIFECYCLE_CHAIN


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def build_attribution(
    *,
    lifecycle_stage: str,
    event_type: str,
    subsystem_id: str,
    discovery_receipt_id: str,
    operator_id: str,
    tenant_id: str,
    governance_mission_id: str | None = None,
    promotion_organ_id: str | None = None,
) -> dict[str, Any]:
    stage_index = LIFECYCLE_CHAIN.index(lifecycle_stage) if lifecycle_stage in LIFECYCLE_CHAIN else -1
    completed = list(LIFECYCLE_CHAIN[: stage_index + 1]) if stage_index >= 0 else []
    return {
        "lifecycle_chain": list(LIFECYCLE_CHAIN),
        "lifecycle_stage": lifecycle_stage,
        "completed_stages": completed,
        "event_type": event_type,
        "subsystem_id": subsystem_id,
        "discovery_receipt_id": discovery_receipt_id,
        "operator_id": operator_id,
        "tenant_id": tenant_id,
        "governance_mission_id": governance_mission_id,
        "promotion_organ_id": promotion_organ_id,
        "contributor_attribution": {
            "operator_id": operator_id,
            "tenant_id": tenant_id,
            "subsystem_id": subsystem_id,
        },
    }


def build_event_id(payload: dict[str, Any]) -> str:
    canonical = {
        "event_type": payload.get("event_type"),
        "operator_id": payload.get("operator_id"),
        "tenant_id": payload.get("tenant_id"),
        "subsystem_id": payload.get("subsystem_id"),
        "discovery_receipt_id": payload.get("discovery_receipt_id"),
        "governance_mission_id": payload.get("governance_mission_id"),
        "promotion_organ_id": payload.get("promotion_organ_id"),
    }
    return sha256(stable_json(canonical).encode("utf-8")).hexdigest()


def resolve_valid_discovery_receipt(
    *,
    tenant_id: str,
    subsystem_id: str,
    discovery_receipt_id: str | None = None,
    runtime_dir: str | None = None,
) -> tuple[dict[str, Any] | None, str]:
    """Fail-closed: subsystem_id must resolve to persisted, HMAC-valid discovery receipt."""
    tenant_norm = normalize_tenant_id(tenant_id)
    sid = str(subsystem_id or "").strip()
    if not sid or len(sid) != 64:
        return None, "discovery_receipt_unresolved: invalid subsystem_id"

    store = SubsystemDiscoveryStore(runtime_dir=runtime_dir, tenant_id=tenant_norm)
    receipt = store.get_by_subsystem_id(sid)
    if receipt is None:
        return None, "discovery_receipt_unresolved: subsystem not discovered"

    ok, reason = verify_subsystem_discovery_receipt(receipt, runtime_dir=runtime_dir)
    if not ok:
        return None, f"discovery_receipt_unresolved: {reason}"

    if str(receipt.get("subsystem_id") or "").strip() != sid:
        return None, "discovery_receipt_unresolved: subsystem_id mismatch"

    if normalize_tenant_id(receipt.get("tenant_id")) != tenant_norm:
        return None, "discovery_receipt_unresolved: tenant mismatch"

    expected_rid = str(discovery_receipt_id or "").strip()
    actual_rid = str(receipt.get("receipt_id") or "").strip()
    if expected_rid and expected_rid != actual_rid:
        return None, "discovery_receipt_unresolved: discovery_receipt_id mismatch"

    return receipt, "ok"


def build_reward_event(
    *,
    event_type: str,
    operator_id: str,
    tenant_id: str,
    subsystem_id: str,
    discovery_receipt_id: str,
    deltas: dict[str, float],
    discovery_receipt: dict[str, Any],
    governance_mission_id: str | None = None,
    promotion_organ_id: str | None = None,
) -> dict[str, Any]:
    from src.ugr.rewards.operator_reward_spec import get_event_spec

    spec = get_event_spec(event_type)
    stage = spec.lifecycle_stage if spec else "reward"
    attribution = build_attribution(
        lifecycle_stage=stage,
        event_type=event_type,
        subsystem_id=subsystem_id,
        discovery_receipt_id=discovery_receipt_id,
        operator_id=operator_id,
        tenant_id=tenant_id,
        governance_mission_id=governance_mission_id,
        promotion_organ_id=promotion_organ_id,
    )
    attribution["discovery_receipt_schema_version"] = discovery_receipt.get("receipt_schema_version")
    event = {
        "event_type": event_type,
        "operator_id": operator_id,
        "tenant_id": tenant_id,
        "subsystem_id": subsystem_id,
        "discovery_receipt_id": discovery_receipt_id,
        "governance_mission_id": governance_mission_id,
        "promotion_organ_id": promotion_organ_id,
        "deltas": dict(deltas),
        "attribution": attribution,
        "issued_at": time.time(),
    }
    event["event_id"] = build_event_id(event)
    return event
