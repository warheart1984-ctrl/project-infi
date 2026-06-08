"""Deterministic policy v1.1 reward delta computation."""

from __future__ import annotations

from typing import Any

from src.ugr.rewards.operator_profile import OperatorProfile
from src.ugr.rewards.operator_reward_spec import (
    EVENT_CAPABILITY_BRIDGE_EXECUTED,
    EVENT_CAPABILITY_MODULE_ADMITTED,
    EVENT_CLOUD_INVARIANT_SET_PASSED,
    EVENT_LIBRARY_PATTERN_MATCHED,
    EVENT_PATTERN_CLAIM_ACCEPTED,
    EVENT_PROOF_PACKET_PUBLISHED,
    EVENT_PROVIDER_ORGAN_ADMITTED,
    EVENT_SUBSTRATE_ENVELOPE_ATTACHED,
    EVENT_SUBSYSTEM_ADOPTED,
    EVENT_SUBSYSTEM_DISCOVERED,
    EVENT_SUBSYSTEM_ORGAN_PROMOTED,
    EVENT_SUBSYSTEM_PROMOTED,
    EVENT_TRUST_BUNDLE_PASSED,
    EVENT_WORKFLOW_CHAIN_COMPLETED,
    EVENT_WORKFLOW_LIBRARY_ADMITTED,
)
from src.ugr.discovery.pod_arc_multiplier import (
    apply_pod_arc_multiplier_to_deltas,
    resolve_pod_arc_context,
)
from src.ugr.rewards.reward_policy import cap_rail_credit_earn, load_reward_policy


def _apply_standing_tier(
    deltas: dict[str, float],
    discovery_receipt: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, float] | None:
    """Scale base deltas by Library Standing tier; return None when denied."""
    from src.ugr.discovery.standing import reward_tier, standing_from_receipt

    tier = reward_tier(standing_from_receipt(discovery_receipt))
    cfg = dict((policy.get("standing") or {}).get(tier) or {})
    if tier == "denied":
        return None
    scaled = dict(deltas)
    rep_mult = float(cfg.get("reputation_multiplier", 1.0))
    rail_mult = float(cfg.get("rail_credits_multiplier", 1.0))
    scaled["reputation"] = float(scaled.get("reputation") or 0) * rep_mult
    scaled["rail_credits"] = float(scaled.get("rail_credits") or 0) * rail_mult
    if tier == "proven":
        bonus = dict(cfg.get("promotion_bonus") or policy.get("promotion") or {})
        scaled["reputation"] += float(bonus.get("reputation") or 0)
        scaled["rail_credits"] += float(bonus.get("rail_credits") or 0)
    scaled["earned_rail_credits"] = scaled["rail_credits"]
    return scaled


def _finalize_deltas(
    deltas: dict[str, float],
    discovery_receipt: dict[str, Any],
    profile: OperatorProfile,
    *,
    policy: dict[str, Any],
) -> dict[str, float]:
    """Apply governance-arc pod multiplier and re-cap rail credits after scaling."""
    receipt = dict(discovery_receipt or {})
    arc = resolve_pod_arc_context(
        spec_payload=dict(receipt.get("payload") or {}),
        receipt=receipt,
        policy=policy,
    )
    if arc.multiplier <= 1.0:
        return deltas
    scaled = apply_pod_arc_multiplier_to_deltas(
        deltas,
        multiplier=arc.multiplier,
        arc_context=arc,
    )
    scaled["rail_credits"] = cap_rail_credit_earn(
        float(scaled.get("reputation") or 0),
        float(scaled.get("rail_credits") or 0),
        profile_reputation=profile.reputation_score,
        policy=policy,
    )
    scaled["earned_rail_credits"] = scaled["rail_credits"]
    return scaled


POLICY_SECTION_BY_EVENT = {
    EVENT_SUBSYSTEM_DISCOVERED: "discovery",
    EVENT_SUBSYSTEM_PROMOTED: "promotion",
    EVENT_SUBSYSTEM_ADOPTED: "adoption",
    EVENT_WORKFLOW_CHAIN_COMPLETED: "workflow",
    EVENT_WORKFLOW_LIBRARY_ADMITTED: "workflow_library",
    EVENT_PROVIDER_ORGAN_ADMITTED: "organ",
    EVENT_SUBSYSTEM_ORGAN_PROMOTED: "organ_promotion",
    EVENT_PROOF_PACKET_PUBLISHED: "proof",
    EVENT_TRUST_BUNDLE_PASSED: "trust_bundle",
    EVENT_CLOUD_INVARIANT_SET_PASSED: "invariant",
    EVENT_CAPABILITY_BRIDGE_EXECUTED: "capability",
    EVENT_CAPABILITY_MODULE_ADMITTED: "capability_module",
    EVENT_PATTERN_CLAIM_ACCEPTED: "substrate",
    EVENT_LIBRARY_PATTERN_MATCHED: "library_pattern_match",
    EVENT_SUBSTRATE_ENVELOPE_ATTACHED: "substrate_envelope",
}


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
        anchor = str(
            discovery_receipt.get("contribution_id") or discovery_receipt.get("subsystem_id") or ""
        )
        multiplier = float(profile.adoption_multipliers.get(anchor) or 1.0)
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
        tiered = _apply_standing_tier(
            {
                "reputation": reputation,
                "rail_credits": rail_credits,
                "earned_rail_credits": rail_credits,
                "adoption_multiplier": adoption_delta,
            },
            discovery_receipt,
            pol,
        )
        if tiered is None:
            return None
        return _finalize_deltas(tiered, discovery_receipt, profile, policy=pol)
    else:
        section = POLICY_SECTION_BY_EVENT.get(event)
        if not section:
            return None
        cfg = dict(pol.get(section) or {})
        reputation = float(cfg.get("reputation") or 0)
        rail_credits = float(cfg.get("rail_credits") or 0)

    rail_credits = cap_rail_credit_earn(
        reputation,
        rail_credits,
        profile_reputation=profile.reputation_score,
        policy=pol,
    )
    tiered = _apply_standing_tier(
        {
            "reputation": reputation,
            "rail_credits": rail_credits,
            "earned_rail_credits": rail_credits,
            "adoption_multiplier": 0.0,
        },
        discovery_receipt,
        pol,
    )
    if tiered is None:
        return None
    return _finalize_deltas(tiered, discovery_receipt, profile, policy=pol)
