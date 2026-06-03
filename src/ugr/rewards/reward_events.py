"""Reward event types, attribution chain, and canonical event IDs."""

from __future__ import annotations

from hashlib import sha256
import json
import time
from typing import Any

from src.ugr.rewards.reward_policy import LIFECYCLE_CHAIN


EVENT_SUBSYSTEM_DISCOVERED = "subsystem_discovered"
EVENT_SUBSYSTEM_PROMOTED = "subsystem_promoted"
EVENT_SUBSYSTEM_ADOPTED = "subsystem_adopted"

STAGE_BY_EVENT = {
    EVENT_SUBSYSTEM_DISCOVERED: "reward",
    EVENT_SUBSYSTEM_PROMOTED: "reward",
    EVENT_SUBSYSTEM_ADOPTED: "reward",
}

REWARD_EVENT_TYPES = frozenset(
    {
        EVENT_SUBSYSTEM_DISCOVERED,
        EVENT_SUBSYSTEM_PROMOTED,
        EVENT_SUBSYSTEM_ADOPTED,
    }
)


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
    """Chain of custody: discovery → proof → receipt → governance → promotion → adoption → attribution → reward."""
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


def lifecycle_stage_for_event(event_type: str) -> str:
    if event_type == EVENT_SUBSYSTEM_DISCOVERED:
        return "reward"
    if event_type == EVENT_SUBSYSTEM_PROMOTED:
        return "reward"
    if event_type == EVENT_SUBSYSTEM_ADOPTED:
        return "reward"
    return "reward"


def build_reward_event(
    *,
    event_type: str,
    operator_id: str,
    tenant_id: str,
    subsystem_id: str,
    discovery_receipt_id: str,
    deltas: dict[str, float],
    governance_mission_id: str | None = None,
    promotion_organ_id: str | None = None,
    lifecycle_stage: str | None = None,
) -> dict[str, Any]:
    stage = lifecycle_stage or lifecycle_stage_for_event(event_type)
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
