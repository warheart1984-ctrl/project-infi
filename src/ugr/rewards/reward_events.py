"""Backward-compatible re-exports — prefer operator_reward_spec and reward_attribution."""

from __future__ import annotations

from src.ugr.rewards.operator_reward_spec import (
    EVENT_SUBSYSTEM_ADOPTED,
    EVENT_SUBSYSTEM_DISCOVERED,
    EVENT_SUBSYSTEM_PROMOTED,
    REWARD_EVENT_TYPES,
)
from src.ugr.rewards.reward_attribution import (
    build_attribution,
    build_event_id,
    build_reward_event,
    stable_json,
)
from src.ugr.rewards.reward_policy import LIFECYCLE_CHAIN

STAGE_BY_EVENT = {
    EVENT_SUBSYSTEM_DISCOVERED: "reward",
    EVENT_SUBSYSTEM_PROMOTED: "reward",
    EVENT_SUBSYSTEM_ADOPTED: "reward",
}


def lifecycle_stage_for_event(event_type: str) -> str:
    return STAGE_BY_EVENT.get(str(event_type or "").strip(), "reward")
