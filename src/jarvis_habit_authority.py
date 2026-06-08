"""Jarvis authority seam for habit-influenced routing (Stage 5)."""

# Mythic: Jarvis Habit Authority
# Engineering: JarvisHabitAuthorityEngine
from __future__ import annotations

from typing import Any
from uuid import uuid4

MODULE_ID = "AAIS-JHA-01"


def authorize_habit_influence(
    plan_or_proposal: dict[str, Any],
    *,
    session_id: str = "global",
) -> dict[str, Any]:
    """Jarvis executive gate for habit-boosted plans — fail-closed."""
    if plan_or_proposal.get("outcome") == "blocked":
        return {
            "authorized": False,
            "reason": plan_or_proposal.get("reason") or "plan_blocked",
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

    receipt_id = f"jarvis-habit-{uuid4().hex[:12]}"
    return {
        "authorized": True,
        "reason": "jarvis_habit_influence_allow",
        "jarvis_receipt_id": receipt_id,
        "session_id": session_id,
        "module_id": MODULE_ID,
        "claim_label": "asserted",
    }
