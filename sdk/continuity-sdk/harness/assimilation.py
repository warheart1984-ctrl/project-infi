"""CAA-1 assimilation harness for SDK experiments."""

from __future__ import annotations

from typing import Any


def run_assimilation_demo() -> dict[str, Any]:
    from src.crk1.mission_006_calibration_assimilation import run_mission_006_calibration_assimilation

    report = run_mission_006_calibration_assimilation()
    return report.to_dict()
