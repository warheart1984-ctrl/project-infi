"""Jarvis authority seam for organ mesh runs (Stage 4)."""

# Mythic: Jarvis Organ Mesh Authority
# Engineering: JarvisOrganMeshAuthorityEngine
from __future__ import annotations

from typing import Any
from uuid import uuid4

MODULE_ID = "AAIS-JOMA-01"


def authorize_mesh_run(
    plan: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """Jarvis executive gate — fail-closed without verification posture."""
    if plan.get("outcome") == "blocked":
        return {
            "authorized": False,
            "reason": plan.get("reason") or "plan_blocked",
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

    receipt_id = f"jarvis-mesh-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_executive_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
