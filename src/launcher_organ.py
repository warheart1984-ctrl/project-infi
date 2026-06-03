"""Launcher Organ — AAIS launcher package posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LCH-01"
ORGAN_VERSION = "launcher_organ.v1"


def build_launcher_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "aais" / "launcher.py").is_file()
    return {
        "launcher_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"launcher={int(present)};read_only=1"[:128],
        "launcher_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
