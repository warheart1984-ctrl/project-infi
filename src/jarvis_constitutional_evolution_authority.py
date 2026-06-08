"""Jarvis authority for charter amendment overlay admission (Stage 17)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.constitutional_evolution_runtime import validate_amendment_against_charter_and_tier5

MODULE_ID = "AAIS-JCEA-01"


def authorize_amendment_overlay_admission(
    amendment: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    validation = validate_amendment_against_charter_and_tier5(amendment)
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
        "reason": "jarvis_amendment_overlay_admission_allow",
        "jarvis_receipt_id": f"jarvis-cev-{uuid4().hex[:12]}",
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
