"""AAIS Doctor Organ — doctor readiness posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-DOC-01"
ORGAN_VERSION = "aais_doctor_organ.v1"


def build_aais_doctor_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "aais" / "__main__.py").is_file()
    return {
        "aais_doctor_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"doctor_entry={int(present)};read_only=1"[:128],
        "doctor_entry_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
