"""Memory Bank Surface Organ — UI binding posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-MBS-01"
ORGAN_VERSION = "memory_bank_surface_organ.v1"


def build_memory_bank_surface_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "frontend" / "src" / "pages" / "MemoryBank.jsx").is_file()
    return {
        "memory_bank_surface_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"memory_bank_ui={int(present)};read_only=1"[:128],
        "memory_bank_surface_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
