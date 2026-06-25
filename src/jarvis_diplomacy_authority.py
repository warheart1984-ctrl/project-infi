"""Jarvis authority seam for inter-substrate diplomacy overlay admission (Stage 15)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.diplomacy.runtime import validate_accord_against_upstream_layers

MODULE_ID = "AAIS-JDPA-01"


def authorize_diplomacy_overlay_admission(
    accord: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    validation = validate_accord_against_upstream_layers(accord)
    if not validation.get("aligned"):
        return {
            "authorized": False,
            "reason": "alignment_validation_failed",
            "violations": validation.get("violations"),
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    receipt_id = f"jarvis-isd-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_diplomacy_overlay_admission_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }


def authorize_diplomacy_influence(
    plan_or_proposal: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    if plan_or_proposal.get("outcome") == "blocked":
        return {
            "authorized": False,
            "reason": plan_or_proposal.get("reason") or "plan_blocked",
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    receipt_id = f"jarvis-isd3-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_diplomacy_influence_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
