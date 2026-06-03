"""Mechanic Handoff Organ — read-only Mechanic chat enforcement posture."""

# Mythic: Mechanic Handoff Organ
# Engineering: MechanicHandoffBridge
from __future__ import annotations

import os
from typing import Any

MODULE_ID = "AAIS-MH-01"
ORGAN_VERSION = "mechanic_handoff_organ.v1"


def build_mechanic_handoff_status(
    *,
    session_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Observe Mechanic case binding and last enforcement without mutating state."""
    metadata = dict(session_metadata or {})
    case_id = str(metadata.get("mechanic_case_id") or "").strip()
    last = dict(metadata.get("mechanic_enforcement_last") or {})
    enforcement_enabled = str(os.environ.get("MECHANIC_ENFORCE_PROFILE") or "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    blocked = bool(last.get("blocked"))
    summary = (
        f"enforcement={enforcement_enabled};case={case_id or 'none'};"
        f"last_blocked={blocked}"
    )[:128]
    return {
        "mechanic_handoff_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "enforcement_enabled": enforcement_enabled,
        "mechanic_case_id": case_id or None,
        "last_enforcement_blocked": blocked,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
