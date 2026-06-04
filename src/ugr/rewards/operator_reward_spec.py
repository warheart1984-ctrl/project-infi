"""Earnable reward events and required anchors per event type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


EVENT_SUBSYSTEM_DISCOVERED = "subsystem_discovered"
EVENT_SUBSYSTEM_PROMOTED = "subsystem_promoted"
EVENT_SUBSYSTEM_ADOPTED = "subsystem_adopted"

REWARD_EVENT_TYPES = frozenset(
    {
        EVENT_SUBSYSTEM_DISCOVERED,
        EVENT_SUBSYSTEM_PROMOTED,
        EVENT_SUBSYSTEM_ADOPTED,
    }
)

LIFECYCLE_CHAIN = (
    "discovery",
    "proof",
    "receipt",
    "governance",
    "promotion",
    "adoption",
    "attribution",
    "reward",
)


@dataclass(frozen=True)
class RewardEventSpec:
    event_type: str
    lifecycle_stage: str
    requires_governance_mission_id: bool = False
    requires_promotion_organ_id: bool = False

    def validate_request(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if self.event_type not in REWARD_EVENT_TYPES:
            errors.append(f"unknown event_type: {self.event_type}")
        if self.requires_governance_mission_id and not str(payload.get("governance_mission_id") or "").strip():
            errors.append("governance_mission_id required")
        if self.requires_promotion_organ_id and not str(payload.get("promotion_organ_id") or "").strip():
            errors.append("promotion_organ_id required")
        if not str(payload.get("subsystem_id") or "").strip():
            errors.append("subsystem_id required")
        if not str(payload.get("operator_id") or "").strip():
            errors.append("operator_id required")
        if not str(payload.get("tenant_id") or "").strip():
            errors.append("tenant_id required")
        return errors


EVENT_SPECS: dict[str, RewardEventSpec] = {
    EVENT_SUBSYSTEM_DISCOVERED: RewardEventSpec(EVENT_SUBSYSTEM_DISCOVERED, "reward"),
    EVENT_SUBSYSTEM_PROMOTED: RewardEventSpec(
        EVENT_SUBSYSTEM_PROMOTED,
        "reward",
        requires_governance_mission_id=True,
        requires_promotion_organ_id=True,
    ),
    EVENT_SUBSYSTEM_ADOPTED: RewardEventSpec(
        EVENT_SUBSYSTEM_ADOPTED,
        "reward",
        requires_promotion_organ_id=True,
    ),
}


def get_event_spec(event_type: str) -> RewardEventSpec | None:
    return EVENT_SPECS.get(str(event_type or "").strip())
