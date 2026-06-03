"""State Hygiene Subsystem — hygiene snapshot posture."""

# Mythic: State Hygiene Organ
# Engineering: StateHygieneEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-SHY-01"
ORGAN_VERSION = "state_hygiene_organ.v1"


def build_state_hygiene_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "src" / "state_hygiene.py").is_file()
    api = root / "src" / "api.py"
    text = api.read_text(encoding="utf-8") if api.is_file() else ""
    route = "/api/jarvis/state-hygiene" in text
    return {
        "state_hygiene_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"hygiene_module={int(present)};route={int(route)}"[:128],
        "state_hygiene_present": present,
        "state_hygiene_route_present": route,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
