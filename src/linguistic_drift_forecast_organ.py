"""Linguistic Drift Forecast Subsystem — forward drift forecast posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LDF-01"
ORGAN_VERSION = "linguistic_drift_forecast_organ.v1"


def build_linguistic_drift_forecast_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_drift_forecast_engine.py"
    ).is_file()
    cli = (root / "tools" / "linguistic_drift_forecast.py").is_file()
    report = (root / "governance" / "linguistic_drift_forecast.v1.json").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    target = "linguistic-drift-forecast:" in m_text
    return {
        "linguistic_drift_forecast_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};cli={int(cli)};report={int(report)}"[:128],
        "drift_forecast_engine_present": engine,
        "drift_forecast_cli_present": cli,
        "drift_forecast_report_present": report,
        "linguistic_drift_forecast_in_makefile": target,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
