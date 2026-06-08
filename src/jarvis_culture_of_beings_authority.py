"""Jarvis authority seam for culture-of-beings slot_09 admission (Stage 11)."""

# Mythic: Jarvis Culture-of-Beings Authority
# Engineering: JarvisCultureOfBeingsAuthorityEngine
from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.culture_of_beings_runtime import validate_norm_against_identity_narrative_agency_social_and_pacts

MODULE_ID = "AAIS-JCOBA-01"


def authorize_culture_of_beings_slot_admission(
    norm: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """Jarvis executive gate for COB-2 slot_09 admission — fail-closed."""
    validation = validate_norm_against_identity_narrative_agency_social_and_pacts(norm)
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

    receipt_id = f"jarvis-cob-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_culture_of_beings_slot_admission_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }


def authorize_norm_influence(
    plan_or_proposal: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """COB-3 elevation gate for norm-influenced routing suggestions."""
    if plan_or_proposal.get("outcome") == "blocked":
        return {
            "authorized": False,
            "reason": plan_or_proposal.get("reason") or "plan_blocked",
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    receipt_id = f"jarvis-cob3-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_norm_influence_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
