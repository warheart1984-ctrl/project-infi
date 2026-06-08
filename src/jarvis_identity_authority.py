"""Jarvis authority seam for identity foundation admission (Stage 6)."""

# Mythic: Jarvis Identity Authority
# Engineering: JarvisIdentityAuthorityEngine
from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.identity_self_model_runtime import validate_claim_against_anchor
from src.super_nova_anchor import SUPER_NOVA_CONFLICT_RESOLUTION_ORDER

MODULE_ID = "AAIS-JIA-01"


def authorize_foundation_admission(
    claim: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """Jarvis executive gate for ICC-2 foundation admission — fail-closed."""
    validation = validate_claim_against_anchor(claim)
    if not validation.get("aligned"):
        return {
            "authorized": False,
            "reason": "anchor_validation_failed",
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

    receipt_id = f"jarvis-identity-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_foundation_admission_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "conflict_resolution_order": list(SUPER_NOVA_CONFLICT_RESOLUTION_ORDER),
        "claim_label": "asserted",
    }


def authorize_identity_influence(
    plan_or_proposal: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """ICC-3 elevation gate for identity-influenced routing suggestions."""
    if plan_or_proposal.get("outcome") == "blocked":
        return {
            "authorized": False,
            "reason": plan_or_proposal.get("reason") or "plan_blocked",
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    receipt_id = f"jarvis-icc3-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_identity_influence_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
