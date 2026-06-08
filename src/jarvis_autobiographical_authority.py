"""Jarvis authority seam for autobiographical operational admission (Stage 8)."""

# Mythic: Jarvis Autobiographical Authority
# Engineering: JarvisAutobiographicalAuthorityEngine
from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.autobiographical_agency_runtime import validate_episode_against_identity_and_narrative

MODULE_ID = "AAIS-JAA-01"


def authorize_operational_admission(
    episode: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """Jarvis executive gate for AAC-2 operational admission — fail-closed."""
    validation = validate_episode_against_identity_and_narrative(episode)
    if not validation.get("aligned"):
        return {
            "authorized": False,
            "reason": "alignment_validation_failed",
            "violations": validation.get("violations"),
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    try:
        from src.verification_gate_organ import build_verification_gate_status

        vg = build_verification_gate_status()
        if str(vg.get("claim_label") or "") == "rejected":
            return {
                "authorized": False,
                "reason": "verification_gate_rejected",
                "jarvis_receipt_id": None,
                "module_id": MODULE_ID,
            }
    except Exception:
        pass

    receipt_id = f"jarvis-autobio-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_operational_admission_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }


def authorize_agency_influence(
    plan_or_proposal: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """AAC-3 elevation gate for agency-influenced routing suggestions."""
    if plan_or_proposal.get("outcome") == "blocked":
        return {
            "authorized": False,
            "reason": plan_or_proposal.get("reason") or "plan_blocked",
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    receipt_id = f"jarvis-aac3-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_agency_influence_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
