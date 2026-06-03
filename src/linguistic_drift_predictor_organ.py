"""Linguistic Drift Predictor Subsystem — hybrid drift scoring posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LDP-01"
ORGAN_VERSION = "linguistic_drift_predictor_organ.v1"


def build_linguistic_drift_predictor_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    tool = (root / "tools" / "linguistic_drift_predictor.py").is_file()
    report = (root / "governance" / "linguistic_drift_report.v1.json").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "linguistic-drift-gate:" in m_text
    return {
        "linguistic_drift_predictor_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"tool={int(tool)};report={int(report)};gate={int(gate)}"[:128],
        "linguistic_drift_predictor_present": tool,
        "drift_report_present": report,
        "linguistic_drift_gate_in_makefile": gate,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
