"""Linguistic Drift Report Subsystem — drift report artifact posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LDRT-01"
ORGAN_VERSION = "linguistic_drift_report_organ.v1"


def build_linguistic_drift_report_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    report = (root / "governance" / "linguistic_drift_report.v1.json").is_file()
    predictor = (root / "tools" / "linguistic_drift_predictor.py").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    return {
        "linguistic_drift_report_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"report={int(report)};predictor={int(predictor)}"[:128],
        "drift_report_present": report,
        "drift_predictor_tool_present": predictor,
        "linguistic_drift_gate_in_makefile": "linguistic-drift-gate:" in m_text,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
