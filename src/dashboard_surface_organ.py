"""Dashboard Surface Organ — UI binding posture."""

# Mythic: Dashboard Surface Organ
# Engineering: DashboardSurfaceInterface
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-DBS-01"
ORGAN_VERSION = "dashboard_surface_organ.v1"


def build_dashboard_surface_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "frontend" / "src" / "pages" / "Dashboard.jsx").is_file()
    return {
        "dashboard_surface_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"dashboard_ui={int(present)};read_only=1"[:128],
        "dashboard_surface_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
