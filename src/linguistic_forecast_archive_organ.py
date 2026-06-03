"""Linguistic Forecast Archive Subsystem — Wave 14 archive retention posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LFA-01"
ORGAN_VERSION = "linguistic_forecast_archive_organ.v1"


def build_linguistic_forecast_archive_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_drift_forecast_engine.py"
    ).is_file()
    archive_dir = root / "governance" / "linguistic_forecast_archive"
    archive_count = len(list(archive_dir.glob("*.v1.json"))) if archive_dir.is_dir() else 0
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    return {
        "linguistic_forecast_archive_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};archives={archive_count}"[:128],
        "forecast_engine_present": engine,
        "archive_dir_present": archive_dir.is_dir(),
        "archive_artifact_count": archive_count,
        "linguistic_calibration_cycle_in_makefile": (
            "linguistic-calibration-cycle:" in m_text
        ),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
