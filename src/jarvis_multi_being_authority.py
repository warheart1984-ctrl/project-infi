"""Jarvis authority seam for multi-being federation-slot admission (Stage 10)."""

# Mythic: Jarvis Multi-Being Authority
# Engineering: JarvisMultiBeingAuthorityEngine
from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.multi_being_continuity_runtime import validate_pact_against_identity_narrative_agency_and_social

MODULE_ID = "AAIS-JMBA-01"


def authorize_federation_slot_admission(
    pact: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """Jarvis executive gate for MBC-2 federation-slot admission — fail-closed."""
    validation = validate_pact_against_identity_narrative_agency_and_social(pact)
    if not validation.get("aligned"):
        return {
            "authorized": False,
            "reason": "alignment_validation_failed",
            "violations": validation.get("violations"),
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    ref = dict(pact.get("counterparty_organism_ref") or {})
    if ref.get("grant_id") and not pact.get("digest_verified") and pact.get("pact_kind") == "cross_machine_peer":
        return {
            "authorized": False,
            "reason": "digest_not_verified_for_cross_machine_peer",
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

    receipt_id = f"jarvis-mbc-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_federation_slot_admission_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }


def authorize_federation_influence(
    plan_or_proposal: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """MBC-3 elevation gate for federation-influenced routing suggestions."""
    if plan_or_proposal.get("outcome") == "blocked":
        return {
            "authorized": False,
            "reason": plan_or_proposal.get("reason") or "plan_blocked",
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    receipt_id = f"jarvis-mbc3-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_federation_influence_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
