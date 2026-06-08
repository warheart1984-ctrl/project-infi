"""Jarvis authority for federated epoch overlay admission (Stage 19)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from src.federated_civilizational_epoch_runtime import validate_federated_epoch_against_upstream

MODULE_ID = "AAIS-JFCE-01"


def authorize_federated_epoch_overlay_admission(
    charter: dict[str, Any],
    *,
    session_id: str = "global",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    validation = validate_federated_epoch_against_upstream(charter, repo_root=repo_root)
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
        "reason": "jarvis_federated_epoch_overlay_admission_allow",
        "jarvis_receipt_id": f"jarvis-fce-{uuid4().hex[:12]}",
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
