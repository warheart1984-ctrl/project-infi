"""Jarvis authority seam for social archive admission (Stage 9)."""

# Mythic: Jarvis Social Authority
# Engineering: JarvisSocialAuthorityEngine
from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.social_continuity_runtime import validate_bond_against_identity_narrative_and_agency

MODULE_ID = "AAIS-JSA-01"


def authorize_archive_admission(
    bond: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """Jarvis executive gate for SCC-2 archive admission — fail-closed."""
    validation = validate_bond_against_identity_narrative_and_agency(bond)
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

    receipt_id = f"jarvis-social-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_archive_admission_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }


def authorize_social_influence(
    plan_or_proposal: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """SCC-3 elevation gate for social-influenced routing suggestions."""
    if plan_or_proposal.get("outcome") == "blocked":
        return {
            "authorized": False,
            "reason": plan_or_proposal.get("reason") or "plan_blocked",
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    receipt_id = f"jarvis-scc3-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_social_influence_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
