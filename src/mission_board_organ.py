"""Mission Board Organ — read-only mission and verification gate posture."""

# Mythic: Mission Board Organ
# Engineering: MissionBoardEngine
from __future__ import annotations

from typing import Any

from src.mission_board import mission_board
from src.verification_gate_organ import build_verification_gate_status

MODULE_ID = "AAIS-MB-01"
ORGAN_VERSION = "mission_board_organ.v1"


def build_mission_board_status(*, session_id: str | None = None) -> dict[str, Any]:
    """Bounded mission board snapshot joined with verification gate organ."""
    snap = mission_board.snapshot(session_id=session_id, limit=12)
    missions = list(snap.get("missions") or [])
    active = sum(1 for m in missions if str(m.get("status") or "") == "active")
    active_mission = snap.get("active_mission") if isinstance(snap.get("active_mission"), dict) else None
    universal_lane_authority = bool(active_mission and str(active_mission.get("status") or "") == "active")
    gate = build_verification_gate_status()
    summary = (
        f"missions={len(missions)};active={active};"
        f"gate={gate.get('gate_decision', 'unknown')}"
    )[:128]
    return {
        "mission_board_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "mission_count": len(missions),
        "active_mission_count": active,
        "preset_count": len(mission_board.list_presets()),
        "universal_lane_authority": universal_lane_authority,
        "active_mission_id": (active_mission or {}).get("id"),
        "verification_gate_decision": gate.get("gate_decision"),
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
