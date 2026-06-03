"""Memory Smith Subsystem — memory curation posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-MSM-01"
ORGAN_VERSION = "memory_smith_organ.v1"


def build_memory_smith_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "src" / "memory_smith.py").is_file()
    return {
        "memory_smith_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"memory_smith={int(present)};read_only=1"[:128],
        "memory_smith_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
