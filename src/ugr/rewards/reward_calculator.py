"""Deterministic policy v1.1 reward delta computation."""

from __future__ import annotations

from typing import Any

from src.ugr.rewards.operator_profile import OperatorProfile
from src.ugr.rewards.operator_reward_spec import (
    EVENT_SUBSYSTEM_ADOPTED,
    EVENT_SUBSYSTEM_DISCOVERED,
    EVENT_SUBSYSTEM_PROMOTED,
)
from src.ugr.rewards.reward_policy import cap_rail_credit_earn, load_reward_policy


def compute_deltas(
    event_type: str,
    discovery_receipt: dict[str, Any],
    profile: OperatorProfile,
    *,
    policy: dict[str, Any] | None = None,
    governance_status: str | None = None,
) -> dict[str, float] | None:
    """Return reputation/rail_credits/adoption_multiplier deltas, or None if event skipped."""
    pol = policy or load_reward_policy()
    event = str(event_type or "").strip()

    if event == EVENT_SUBSYSTEM_DISCOVERED:
        disc = dict(pol.get("discovery") or {})
        reputation = float(disc.get("reputation") or 0)
        rail_credits = float(disc.get("rail_credits") or 0)
        bonus = dict(disc.get("search_efficiency_bonus") or {})
        if str(discovery_receipt.get("discovery_mode") or "") == "search":
            if int(discovery_receipt.get("search_attempts") or 0) <= int(bonus.get("max_attempts") or 8):
                reputation += float(bonus.get("reputation") or 0)
                rail_credits += float(bonus.get("rail_credits") or 0)
    elif event == EVENT_SUBSYSTEM_PROMOTED:
        if str(governance_status or "").lower() not in {"ok", "completed"}:
            return None
        promo = dict(pol.get("promotion") or {})
        reputation = float(promo.get("reputation") or 0)
        rail_credits = float(promo.get("rail_credits") or 0)
    elif event == EVENT_SUBSYSTEM_ADOPTED:
        adopt = dict(pol.get("adoption") or {})
        multiplier = float(profile.adoption_multipliers.get(str(discovery_receipt.get("subsystem_id") or "")) or 1.0)
        reputation = float(adopt.get("reputation") or 0)
        if adopt.get("reputation_scales_with_multiplier", True):
            reputation = reputation * multiplier
        rail_credits = float(adopt.get("rail_credits") or 0)
        adoption_delta = float(adopt.get("multiplier_increment") or 0)
        rail_credits = cap_rail_credit_earn(
            reputation,
            rail_credits,
            profile_reputation=profile.reputation_score,
            policy=pol,
        )
        return {
            "reputation": reputation,
            "rail_credits": rail_credits,
            "adoption_multiplier": adoption_delta,
        }
    else:
        return None

    rail_credits = cap_rail_credit_earn(
        reputation,
        rail_credits,
        profile_reputation=profile.reputation_score,
        policy=pol,
    )
    return {
        "reputation": reputation,
        "rail_credits": rail_credits,
        "adoption_multiplier": 0.0,
    }
