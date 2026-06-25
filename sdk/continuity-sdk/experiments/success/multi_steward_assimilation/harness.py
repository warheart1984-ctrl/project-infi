"""Multi-steward assimilation demo."""

from __future__ import annotations

from typing import Any


def run() -> dict[str, Any]:
    from src.crk1.mission_005_calibration_lineage_stress import run_mission_005_calibration_lineage_stress

    m005 = run_mission_005_calibration_lineage_stress()
    return {
        "question": "Do multiple stewards converge toward correction after replay?",
        "passed": m005.passed and m005.crr_count >= 3,
        "stewards": m005.stewards,
    }
