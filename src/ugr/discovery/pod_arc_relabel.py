"""Narrative-only governance arc relabeling — no reward or multiplier changes."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import uuid4

from src.ugr.discovery.discovery_pod_ledger import (
    EVENT_POD_ARC_RELABELLED,
    LEDGER_ID,
    LEDGER_VERSION,
    DiscoveryPodLedger,
    _utc_now_iso,
)
from src.ugr.discovery.pod_arc_multiplier import (
    TIER_BEYOND_BODY,
    TIER_CIVILIZATIONAL,
    arc_multipliers_from_policy,
    normalize_arc_tier,
)
from src.ugr.rewards.reward_policy import load_reward_policy


def _normalize_relabel_tier(tier: str) -> str:
    return normalize_arc_tier(tier, default=TIER_BEYOND_BODY)


def _latest_relabel(
    ledger: DiscoveryPodLedger,
    *,
    pod_id: str,
    contribution_id: str | None = None,
) -> dict[str, Any] | None:
    rows = ledger.list_pod_arc_relabelled(pod_id=pod_id)
    if contribution_id:
        cid = str(contribution_id).strip()
        scoped = [r for r in rows if str(r.get("contribution_id") or "") == cid]
        if scoped:
            return scoped[-1]
    return rows[-1] if rows else None


def relabel_pod_arc_tier(
    *,
    pod_id: str,
    arc_tier: str,
    contribution_id: str | None = None,
    narrative_note: str = "",
    ledger: DiscoveryPodLedger | None = None,
) -> dict[str, Any]:
    """
    Append a pod_arc_relabelled event — narrative registry display only.

    Does not modify operator balances, reward ledger, or prior ledger rows.
    """
    pod_ledger = ledger or DiscoveryPodLedger()
    pod_row = pod_ledger.get_by_pod_id(pod_id)
    if not pod_row:
        return {"ok": False, "errors": [f"unknown pod_id: {pod_id}"]}

    operator_id = str(pod_row.get("operator_id") or "").strip()
    proven_events = pod_ledger.list_pod_proven(pod_id=pod_id)
    cid = str(contribution_id or "").strip()
    if not cid and proven_events:
        cid = str(proven_events[-1].get("contribution_id") or "").strip()

    new_tier = _normalize_relabel_tier(arc_tier)
    policy = load_reward_policy()
    multipliers = arc_multipliers_from_policy(policy)
    display_multiplier = float(pod_ledger.arc_stats(pod_id).get("pod_reward_multiplier") or 1.0)
    tier_multiplier = float(multipliers.get(new_tier) or display_multiplier)
    # Narrative relabel never reduces the economic multiplier already earned.
    preserved_multiplier = max(display_multiplier, tier_multiplier)

    prior = pod_ledger.arc_stats(pod_id)
    previous_tier = str(prior.get("governance_arc_tier") or "none")

    existing = _latest_relabel(pod_ledger, pod_id=pod_id, contribution_id=cid or None)
    if existing and str(existing.get("governance_arc_tier") or "") == new_tier:
        note = str(existing.get("narrative_note") or "")
        if not narrative_note or note == narrative_note:
            return {
                "ok": True,
                "skipped": True,
                "idempotent": True,
                "pod_id": pod_id,
                "contribution_id": cid or None,
                "governance_arc_tier": new_tier,
                "pod_reward_multiplier": preserved_multiplier,
                "previous_governance_arc_tier": existing.get("previous_governance_arc_tier"),
                "narrative_note": note,
            }

    relabel_key = hashlib.sha256(
        f"pod_arc_relabelled:{pod_id}:{cid}:{new_tier}:{narrative_note}".encode()
    ).hexdigest()[:16]
    pod_event_id = f"parl-{uuid4().hex[:12]}"

    pod_record: dict[str, Any] = {
        "event_id": pod_event_id,
        "event_type": EVENT_POD_ARC_RELABELLED,
        "ledger_id": LEDGER_ID,
        "ledger_version": LEDGER_VERSION,
        "recorded_at_utc": _utc_now_iso(),
        "pod_id": pod_id,
        "display_name": pod_row.get("display_name"),
        "operator_id": operator_id,
        "governance_arc_tier": new_tier,
        "previous_governance_arc_tier": previous_tier,
        "pod_reward_multiplier": preserved_multiplier,
        "narrative_only": True,
        "relabel_key": relabel_key,
        "arc_signals": [f"relabel:{new_tier}"],
    }
    if cid:
        pod_record["contribution_id"] = cid
    if narrative_note:
        pod_record["narrative_note"] = narrative_note

    with pod_ledger._lock:
        pod_ledger.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with pod_ledger.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(pod_record, sort_keys=True, default=str) + "\n")
        pod_ledger.sync_registry()

    return {
        "ok": True,
        "pod_id": pod_id,
        "operator_id": operator_id,
        "contribution_id": cid or None,
        "governance_arc_tier": new_tier,
        "previous_governance_arc_tier": previous_tier,
        "pod_reward_multiplier": preserved_multiplier,
        "narrative_only": True,
        "narrative_note": narrative_note,
        "pod_event_id": pod_event_id,
    }
