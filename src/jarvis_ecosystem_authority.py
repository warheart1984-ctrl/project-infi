"""Jarvis authority seam for constitutional ecosystem slot_08 admission (Stage 12)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.constitutional_ecosystem_runtime import validate_charter_against_upstream_layers

MODULE_ID = "AAIS-JECA-01"


def authorize_ecosystem_slot_admission(
    charter: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    validation = validate_charter_against_upstream_layers(charter)
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

        if str(build_verification_gate_status().get("claim_label") or "") == "rejected":
            return {"authorized": False, "reason": "verification_gate_rejected", "jarvis_receipt_id": None, "module_id": MODULE_ID}
    except Exception:
        pass
    receipt_id = f"jarvis-cec-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_ecosystem_slot_admission_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }


def authorize_ecosystem_influence(
    plan_or_proposal: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    if plan_or_proposal.get("outcome") == "blocked":
        return {"authorized": False, "reason": plan_or_proposal.get("reason") or "plan_blocked", "jarvis_receipt_id": None, "module_id": MODULE_ID}
    receipt_id = f"jarvis-cec3-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_ecosystem_influence_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
