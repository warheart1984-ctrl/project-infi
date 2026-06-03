"""V10 Runtime Subsystem — V10 runtime snapshot posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-V10R-01"
ORGAN_VERSION = "v10_runtime_organ.v1"


def build_v10_runtime_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "src" / "v10_runtime.py").is_file()
    api = root / "src" / "api.py"
    text = api.read_text(encoding="utf-8") if api.is_file() else ""
    routes = sum(
        1
        for marker in ("/api/jarvis/v10-runtime", "/api/jarvis/v10-runtime/events")
        if marker in text
    )
    return {
        "v10_runtime_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"v10_runtime={int(present)};routes={routes}"[:128],
        "v10_runtime_present": present,
        "v10_runtime_routes_present": routes,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
