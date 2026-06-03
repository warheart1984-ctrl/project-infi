"""Creative Console Interface Subsystem — v9/v10 UI binding posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-CCI-01"
ORGAN_VERSION = "creative_console_interface_organ.v1"


def build_creative_console_interface_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    pages = root / "frontend" / "src" / "pages"
    jarvis = pages / "JarvisConsole.jsx"
    dashboard = pages / "Dashboard.jsx"
    j_text = jarvis.read_text(encoding="utf-8") if jarvis.is_file() else ""
    d_text = dashboard.read_text(encoding="utf-8") if dashboard.is_file() else ""
    v9_refs = sum(1 for token in ("v9_runtime", "v9Runtime") if token in j_text or token in d_text)
    v10_refs = sum(1 for token in ("v10_runtime", "v10Runtime") if token in j_text or token in d_text)
    return {
        "creative_console_interface_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"v9_ui_refs={v9_refs};v10_ui_refs={v10_refs}"[:128],
        "jarvis_console_present": jarvis.is_file(),
        "dashboard_present": dashboard.is_file(),
        "v9_ui_refs": v9_refs,
        "v10_ui_refs": v10_refs,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
