"""Jarvis authority seam for governance membrane slot_10 admission (Stage 13)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.multi_organism_governance_membrane_runtime import validate_policy_against_upstream_layers

MODULE_ID = "AAIS-JMGA-01"


def authorize_membrane_slot_admission(
    policy: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    validation = validate_policy_against_upstream_layers(policy)
    if not validation.get("aligned"):
        return {
            "authorized": False,
            "reason": "alignment_validation_failed",
            "violations": validation.get("violations"),
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    receipt_id = f"jarvis-mgm-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_membrane_slot_admission_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }


def authorize_membrane_influence(
    plan_or_proposal: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    if plan_or_proposal.get("outcome") == "blocked":
        return {"authorized": False, "reason": plan_or_proposal.get("reason") or "plan_blocked", "jarvis_receipt_id": None, "module_id": MODULE_ID}
    receipt_id = f"jarvis-mgm3-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_membrane_influence_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
