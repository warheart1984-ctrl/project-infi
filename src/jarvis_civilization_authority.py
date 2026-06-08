"""Jarvis authority for civilization overlay admission (Stage 18)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.governed_civilization_runtime import validate_civilization_against_upstream_envelope

MODULE_ID = "AAIS-JGCA-01"


def authorize_civilization_overlay_admission(
    civilization: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    validation = validate_civilization_against_upstream_envelope(civilization)
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
        "reason": "jarvis_civilization_overlay_admission_allow",
        "jarvis_receipt_id": f"jarvis-gcv-{uuid4().hex[:12]}",
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
