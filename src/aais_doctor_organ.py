"""AAIS Doctor Organ — doctor readiness posture."""

# Mythic: Aais Doctor Organ
# Engineering: AaisDoctorEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-DOC-01"
ORGAN_VERSION = "aais_doctor_organ.v1"


def build_aais_doctor_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "aais" / "__main__.py").is_file()
    runtime_summary: dict[str, Any] = {}
    try:
        from aais.launcher import runtime_summary as doctor_runtime_summary

        runtime_summary = dict(doctor_runtime_summary(data_dir=None) or {})
    except Exception as exc:
        runtime_summary = {"error": str(exc)[:200]}
    healthy = bool(runtime_summary.get("ok", runtime_summary.get("healthy", present)))
    return {
        "aais_doctor_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"doctor_entry={int(present)};runtime_ok={int(healthy)}"[:128],
        "doctor_entry_present": present,
        "runtime_summary": runtime_summary,
        "healthy": healthy,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted" if healthy else "debt",
    }
