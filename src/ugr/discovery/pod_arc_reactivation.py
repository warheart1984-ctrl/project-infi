"""Retroactively apply governance-arc pod reward multipliers to prior proven rewards."""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any
from uuid import uuid4

from src.ugr.discovery.discovery_pod_ledger import (
    EVENT_POD_ARC_REACTIVATED,
    LEDGER_ID,
    LEDGER_VERSION,
    DiscoveryPodLedger,
    _utc_now_iso,
)
from src.ugr.discovery.pod_arc_multiplier import (
    TIER_BEYOND_BODY,
    TIER_CIVILIZATIONAL,
    PodArcContext,
    apply_pod_arc_multiplier_to_deltas,
    arc_multipliers_from_policy,
    normalize_arc_tier,
    tier_rank,
)
from src.ugr.rewards.reward_ledger import RewardLedger
from src.ugr.rewards.reward_policy import load_reward_policy


def _arc_context_for_tier(tier: str, *, policy: dict[str, Any] | None = None) -> PodArcContext:
    pol = policy or load_reward_policy()
    multipliers = arc_multipliers_from_policy(pol)
    tier_key = normalize_arc_tier(tier, default=TIER_CIVILIZATIONAL)
    return PodArcContext(
        tier=tier_key,
        multiplier=float(multipliers.get(tier_key) or 10.0),
        signals=[f"reactivation:{tier_key}"],
    )


def _find_original_reward(
    ledger: RewardLedger,
    *,
    operator_id: str,
    contribution_id: str,
) -> dict[str, Any] | None:
    rows = ledger.list_events(operator_id=operator_id, contribution_id=contribution_id, limit=200)
    for row in reversed(rows):
        if str(row.get("status") or "") in {"issued", ""}:
            deltas = dict(row.get("deltas") or {})
            if float(deltas.get("reputation") or 0) > 0:
                return row
    return None


def _has_arc_reactivation(ledger: DiscoveryPodLedger, *, contribution_id: str) -> bool:
    for row in ledger.list_entries(event_type=EVENT_POD_ARC_REACTIVATED):
        if str(row.get("contribution_id") or "") == str(contribution_id or "").strip():
            return True
    return False


def reactivate_pod_arc_multiplier(
    *,
    pod_id: str,
    contribution_id: str | None = None,
    arc_tier: str = TIER_CIVILIZATIONAL,
    runtime_dir: str | None = None,
    ledger: DiscoveryPodLedger | None = None,
) -> dict[str, Any]:
    """
    Apply the governance-arc multiplier delta to a proven contribution that was
    rewarded before arc scaling existed (or without arc metadata on the receipt).
    """
    pod_ledger = ledger or DiscoveryPodLedger()
    reward_runtime = runtime_dir or os.getenv("AAIS_RUNTIME_DIR")
    pod_row = pod_ledger.get_by_pod_id(pod_id)
    if not pod_row:
        return {"ok": False, "errors": [f"unknown pod_id: {pod_id}"]}

    operator_id = str(pod_row.get("operator_id") or "").strip()
    proven_events = pod_ledger.list_pod_proven(pod_id=pod_id)
    if not proven_events:
        return {"ok": False, "errors": [f"no proven events for pod {pod_id}"]}

    cid = str(contribution_id or "").strip()
    if not cid:
        cid = str(proven_events[-1].get("contribution_id") or "").strip()
    if not cid:
        return {"ok": False, "errors": ["contribution_id could not be resolved"]}

    if _has_arc_reactivation(pod_ledger, contribution_id=cid):
        arc = pod_ledger.arc_stats(pod_id)
        return {
            "ok": True,
            "skipped": True,
            "idempotent": True,
            "pod_id": pod_id,
            "contribution_id": cid,
            "governance_arc_tier": arc.get("governance_arc_tier"),
            "pod_reward_multiplier": arc.get("pod_reward_multiplier"),
        }

    proven_row = next(
        (r for r in proven_events if str(r.get("contribution_id") or "") == cid),
        proven_events[-1],
    )
    tenant_id = str(proven_row.get("tenant_id") or "global").strip()
    receipt_id = str(proven_row.get("receipt_id") or "").strip()

    policy = load_reward_policy()
    arc = _arc_context_for_tier(arc_tier, policy=policy)

    existing_arc = pod_ledger.arc_stats(pod_id)
    if (
        tier_rank(str(existing_arc.get("governance_arc_tier") or ""))
        >= tier_rank(arc.tier)
        and float(existing_arc.get("pod_reward_multiplier") or 1.0) >= arc.multiplier
    ):
        return {
            "ok": True,
            "skipped": True,
            "skip_reason": "arc_multiplier_already_active",
            "pod_id": pod_id,
            "contribution_id": cid,
            **existing_arc,
        }

    reward_ledger = RewardLedger(runtime_dir=reward_runtime, tenant_id=tenant_id)
    original = _find_original_reward(
        reward_ledger,
        operator_id=operator_id,
        contribution_id=cid,
    )
    if original is None:
        return {
            "ok": False,
            "errors": [f"no issued reward found for contribution {cid}"],
        }

    original_deltas = dict(original.get("deltas") or {})
    base_rep = float(original_deltas.get("reputation") or 0)
    base_credits = float(
        original_deltas.get("earned_rail_credits") or original_deltas.get("rail_credits") or 0
    )
    if base_rep <= 0:
        return {"ok": False, "errors": ["original reward has zero reputation delta"]}

    scaled = apply_pod_arc_multiplier_to_deltas(
        {
            "reputation": base_rep,
            "rail_credits": base_credits,
            "earned_rail_credits": base_credits,
        },
        multiplier=arc.multiplier,
        arc_context=arc,
    )
    adj_rep = float(scaled["reputation"]) - base_rep
    adj_credits = float(scaled.get("earned_rail_credits") or scaled.get("rail_credits") or 0) - base_credits
    if adj_rep <= 0 and adj_credits <= 0:
        return {
            "ok": True,
            "skipped": True,
            "skip_reason": "no_adjustment_needed",
            "pod_id": pod_id,
            "contribution_id": cid,
        }

    profile = reward_ledger.load_balances(operator_id)
    issued_at = time.time()
    profile.apply_deltas(
        reputation=adj_rep,
        earned_rail_credits=adj_credits,
        adoption_multiplier_delta=0.0,
        contribution_id=cid,
        issued_at=issued_at,
    )
    reward_ledger.save_balances(profile)

    base_event_id = str(original.get("event_id") or "")
    reactivation_id = hashlib.sha256(
        f"pod_arc_reactivated:{pod_id}:{cid}:{arc.tier}:{base_event_id}".encode()
    ).hexdigest()

    adjustment_event = {
        "event_id": reactivation_id,
        "event_type": EVENT_POD_ARC_REACTIVATED,
        "operator_id": operator_id,
        "tenant_id": tenant_id,
        "contribution_id": cid,
        "discovery_receipt_id": receipt_id,
        "issued_at": issued_at,
        "deltas": {
            "reputation": adj_rep,
            "rail_credits": adj_credits,
            "earned_rail_credits": adj_credits,
            "pod_reward_multiplier": arc.multiplier,
            "governance_arc_tier": arc.tier,
        },
        "attribution": {
            "reactivation_of_event_id": base_event_id,
            "pod_id": pod_id,
            "arc_tier": arc.tier,
            "base_reputation": base_rep,
            "scaled_reputation": float(scaled["reputation"]),
        },
    }
    reward_ledger.append_event(adjustment_event)

    pod_event_id = f"parc-{uuid4().hex[:12]}"
    pod_record = {
        "event_id": pod_event_id,
        "event_type": EVENT_POD_ARC_REACTIVATED,
        "ledger_id": LEDGER_ID,
        "ledger_version": LEDGER_VERSION,
        "recorded_at_utc": _utc_now_iso(),
        "pod_id": pod_id,
        "display_name": pod_row.get("display_name"),
        "operator_id": operator_id,
        "tenant_id": tenant_id,
        "contribution_id": cid,
        "receipt_id": receipt_id,
        "reputation_adjustment": adj_rep,
        "rail_credits_adjustment": adj_credits,
        "reputation_awarded": float(scaled["reputation"]),
        "rail_credits_awarded": float(scaled.get("earned_rail_credits") or 0),
        "reactivation_of_event_id": base_event_id,
        "reward_event_id": reactivation_id,
        **arc.to_dict(),
    }

    with pod_ledger._lock:
        pod_ledger.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with pod_ledger.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(pod_record, sort_keys=True, default=str) + "\n")
        pod_ledger.sync_registry()

    return {
        "ok": True,
        "pod_id": pod_id,
        "operator_id": operator_id,
        "contribution_id": cid,
        "governance_arc_tier": arc.tier,
        "pod_reward_multiplier": arc.multiplier,
        "reputation_adjustment": adj_rep,
        "rail_credits_adjustment": adj_credits,
        "profile": profile.to_dict(),
        "reward_event_id": reactivation_id,
        "pod_event_id": pod_event_id,
    }
