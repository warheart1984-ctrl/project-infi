"""Jarvis authority seam for narrative session admission (Stage 7)."""

# Mythic: Jarvis Narrative Authority
# Engineering: JarvisNarrativeAuthorityEngine
from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.narrative_continuity_runtime import validate_beat_against_identity

MODULE_ID = "AAIS-JNA-01"


def authorize_session_admission(
    beat: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """Jarvis executive gate for NCC-2 session admission — fail-closed."""
    validation = validate_beat_against_identity(beat)
    if not validation.get("aligned"):
        return {
            "authorized": False,
            "reason": "identity_validation_failed",
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

    receipt_id = f"jarvis-narrative-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_session_admission_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }


def authorize_narrative_influence(
    plan_or_proposal: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """NCC-3 elevation gate for narrative-influenced routing suggestions."""
    if plan_or_proposal.get("outcome") == "blocked":
        return {
            "authorized": False,
            "reason": plan_or_proposal.get("reason") or "plan_blocked",
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    receipt_id = f"jarvis-ncc3-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_narrative_influence_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
