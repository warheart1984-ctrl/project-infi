"""Forensic Triangulation capability — correlate forensic claims per case_id."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from src.alt3_lineage import record_alt3_lineage
from src.phase_gate import (
    ComponentNotRegisteredError,
    GovernedComponent,
    Phase,
    PhaseViolationError,
    assert_executable,
    get_component,
    register_component,
)
from triangulation.common import FIXTURE_ROOT
from triangulation.correlate import correlate_case

FORENSIC_TRIANGULATION_CAPABILITY_COMPONENT_ID = "jarvis.capability.forensic_triangulation"

ForensicTriangulationCapability = {
    "name": "forensic_triangulation",
    "version": "v1",
    "actions": ["correlate"],
}


def ensure_forensic_triangulation_capability_registered() -> None:
    try:
        get_component(FORENSIC_TRIANGULATION_CAPABILITY_COMPONENT_ID)
        return
    except ComponentNotRegisteredError:
        pass
    register_component(
        GovernedComponent(
            component_id=FORENSIC_TRIANGULATION_CAPABILITY_COMPONENT_ID,
            name="Forensic Triangulation Capability",
            component_type="capability",
            phase=Phase.VALIDATED,
            allowed_contexts=["operator_runtime", "test_harness"],
            notes="Structured correlate tool for Mechanic, Scorpion, and Slingshot claims.",
            validation_metadata=deepcopy(ForensicTriangulationCapability),
        )
    )


def _lineage_after(request: dict[str, Any], action: str, payload: dict[str, Any]) -> None:
    record_alt3_lineage(
        subsystem="forensic_triangulation",
        action=action,
        mission_id=(request or {}).get("mission_id"),
        session_id=(request or {}).get("session_id"),
        payload=payload,
    )


def run_forensic_triangulation_capability(request: dict[str, Any]) -> dict[str, Any]:
    ensure_forensic_triangulation_capability_registered()
    runtime_context = str((request or {}).get("runtime_context") or "operator_runtime")
    try:
        assert_executable(FORENSIC_TRIANGULATION_CAPABILITY_COMPONENT_ID, runtime_context)
    except PhaseViolationError as exc:
        return {
            "ok": False,
            "status": "rejected",
            "error_type": "AuthorityRejected",
            "message": str(exc),
        }

    action = str((request or {}).get("action") or "correlate").strip().lower()
    if action != "correlate":
        return {
            "ok": False,
            "status": "rejected",
            "error_type": "UnsupportedAction",
            "message": f"unsupported action: {action}",
        }

    case_id = str((request or {}).get("case_id") or "").strip()
    if not case_id:
        return {
            "ok": False,
            "status": "rejected",
            "error_type": "ValidationError",
            "message": "case_id is required",
        }

    fixture = (request or {}).get("fixture")
    triangulation_root = (request or {}).get("triangulation_root")
    mechanic_root = (request or {}).get("mechanic_root")
    scorpion_root = (request or {}).get("scorpion_root")
    slingshot_root = (request or {}).get("slingshot_root")

    fixture_root = None
    if fixture:
        fixture_root = FIXTURE_ROOT / str(fixture)

    try:
        payload = correlate_case(
            case_id,
            mechanic_root=Path(mechanic_root).expanduser() if mechanic_root else None,
            scorpion_root=Path(scorpion_root).expanduser() if scorpion_root else None,
            slingshot_root=Path(slingshot_root).expanduser() if slingshot_root else None,
            triangulation_root=Path(triangulation_root).expanduser() if triangulation_root else None,
            fixture_root=fixture_root,
        )
        result = {
            "ok": True,
            "status": "completed",
            "case_id": case_id,
            "triangulation": payload,
            "edge_count": len(payload.get("correlation_edges") or []),
        }
        _lineage_after(request, action, {"case_id": case_id, "edge_count": result["edge_count"]})
        return result
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "status": "failed",
            "error_type": type(exc).__name__,
            "message": str(exc),
        }
