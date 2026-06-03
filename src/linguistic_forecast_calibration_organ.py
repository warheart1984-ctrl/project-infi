"""Linguistic Forecast Calibration Subsystem — Wave 13 calibration posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LFC-02"
ORGAN_VERSION = "linguistic_forecast_calibration_organ.v1"


def build_linguistic_forecast_calibration_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_forecast_calibration_engine.py"
    ).is_file()
    policy = (
        root / "governance" / "linguistic_forecast_calibration_policy.v1.json"
    ).is_file()
    report = False
    reg_path = root / "governance" / "meta_linguistic_registry.v1.json"
    if reg_path.is_file():
        import json

        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        ref = reg.get("last_calibration_report")
        if ref and (root / ref).is_file():
            report = True
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    target = "linguistic-calibration-cycle:" in m_text
    return {
        "linguistic_forecast_calibration_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};policy={int(policy)};report={int(report)}"[:128],
        "calibration_engine_present": engine,
        "calibration_policy_present": policy,
        "last_calibration_report_present": report,
        "linguistic_calibration_cycle_in_makefile": target,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
