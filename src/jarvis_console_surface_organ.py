"""Jarvis Console Surface Organ — UI binding posture."""

# Mythic: Jarvis Console Surface Organ
# Engineering: JarvisConsoleSurfaceInterface
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-JCS-01"
ORGAN_VERSION = "jarvis_console_surface_organ.v1"


def build_jarvis_console_surface_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "frontend" / "src" / "pages" / "JarvisConsole.jsx").is_file()
    return {
        "jarvis_console_surface_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"console_ui={int(present)};read_only=1"[:128],
        "console_surface_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
