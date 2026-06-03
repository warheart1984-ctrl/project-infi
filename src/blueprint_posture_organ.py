"""Blueprint Posture Subsystem — blueprint snapshot posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-BPP-01"
ORGAN_VERSION = "blueprint_posture_organ.v1"


def build_blueprint_posture_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "src" / "aais_blueprint.py").is_file()
    api = root / "src" / "api.py"
    text = api.read_text(encoding="utf-8") if api.is_file() else ""
    route = "/api/jarvis/blueprint" in text
    return {
        "blueprint_posture_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"blueprint={int(present)};route={int(route)}"[:128],
        "blueprint_module_present": present,
        "blueprint_route_present": route,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
