"""Jarvis authority for norm federation overlay admission (Stage 16)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.norm_federation_runtime import validate_treaty_against_norms_charters_and_membrane

MODULE_ID = "AAIS-JNFA-01"


def authorize_norm_federation_overlay_admission(
    treaty: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    validation = validate_treaty_against_norms_charters_and_membrane(treaty)
    if not validation.get("aligned"):
        return {
            "authorized": False,
            "reason": "alignment_validation_failed",
            "violations": validation.get("violations"),
            "jarvis_receipt_id": None,
            "module_id": MODULE_ID,
        }
    return {
        "authorized": True,
        "reason": "jarvis_norm_federation_overlay_admission_allow",
        "jarvis_receipt_id": f"jarvis-nfd-{uuid4().hex[:12]}",
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
