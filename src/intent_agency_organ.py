"""Intent Agency Organ — live posture from autobiographical agency runtime."""

# Mythic: Intent Agency Organ
# Engineering: IntentAgencyEngine
from __future__ import annotations

from typing import Any


def build_intent_agency_status() -> dict[str, Any]:
    """Read-only agency posture from live runtime + intent store."""
    try:
        from src.autobiographical_agency_runtime import autobiographical_agency_runtime

        posture = autobiographical_agency_runtime.autobiographical_posture()
        snapshot = autobiographical_agency_runtime.autobiographical_snapshot()
        intent = dict(snapshot.get("intent_summary") or {})
        commitment_count = int(intent.get("active_commitment_count") or 0)
        agency_claim = "asserted"
        if commitment_count > 0 and posture.get("identity_aligned"):
            agency_claim = "proven"
        return {
            "intent_agency_organ_version": "intent_agency_organ.v1",
            "agency_note": str(intent.get("agency_note") or "")[:220],
            "active_tension_count": 0,
            "active_commitment_count": commitment_count,
            "agency_claim_posture": agency_claim,
            "adopted_episodes": posture.get("adopted_episodes", 0),
            "ongoing_work_count": posture.get("ongoing_work_count", 0),
            "identity_aligned": posture.get("identity_aligned", True),
            "narrative_aligned": posture.get("narrative_aligned", True),
            "cisiv_stage": "implementation",
            "claim_label": agency_claim,
            "read_only": True,
            "live_runtime": True,
        }
    except Exception as exc:
        return {
            "intent_agency_organ_version": "intent_agency_organ.v1",
            "agency_note": "",
            "active_tension_count": 0,
            "active_commitment_count": 0,
            "agency_claim_posture": "rejected",
            "cisiv_stage": "implementation",
            "claim_label": "rejected",
            "read_only": True,
            "error": str(exc)[:200],
        }
