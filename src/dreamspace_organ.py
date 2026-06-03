"""Dreamspace Organ — governed opt-in reflective runtime posture."""

# Mythic: Dreamspace Organ
# Engineering: DreamspaceOrganGate
from __future__ import annotations

from typing import Any

from src.dreamspace import dreamspace

MODULE_ID = "AAIS-DSO-01"
ORGAN_VERSION = "dreamspace_organ.v1"


def build_dreamspace_organ_status() -> dict[str, Any]:
    summary = dreamspace.snapshot()
    status = str(summary.get("status") or "stopped")
    governed_active = status in {"running", "paused"}
    return {
        "dreamspace_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"status={status};governed=1;opt_in=1"[:128],
        "dreamspace_status": status,
        "governed_activation": True,
        "default_on": False,
        "opt_in_required": True,
        "governed_active": governed_active,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
