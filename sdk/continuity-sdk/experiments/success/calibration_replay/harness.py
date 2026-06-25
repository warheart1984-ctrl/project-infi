"""Calibration replay success demo.

Question: Did prediction improve after correction?
Artifacts: GRR-1, CRR-1, CAA-1 (via Mission #006).
"""

from __future__ import annotations

from typing import Any


def run() -> dict[str, Any]:
    from src.crk1.mission_006_calibration_assimilation import run_mission_006_calibration_assimilation

    report = run_mission_006_calibration_assimilation()
    return {
        "question": "Did prediction improve after correction?",
        "passed": report.passed,
        "assimilation_delta": report.assimilation_delta,
        "caa1_receipt_id": report.cxd_id,
    }
