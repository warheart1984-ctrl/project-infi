"""Operator Workspace Subsystem — workspace API posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-OWS-01"
ORGAN_VERSION = "operator_workspace_organ.v1"


def build_operator_workspace_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    api = root / "src" / "api.py"
    text = api.read_text(encoding="utf-8") if api.is_file() else ""
    routes = sum(
        1
        for marker in (
            "/api/jarvis/workspace/projects",
            "/api/jarvis/workspace/search",
            "/api/jarvis/workspace/file",
        )
        if marker in text
    )
    return {
        "operator_workspace_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"workspace_routes={routes};read_only=1"[:128],
        "workspace_routes_present": routes,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
