"""Assimilation harness tests (SDK layer)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.crk1.mission_006_calibration_assimilation import run_mission_006_calibration_assimilation


def test_sdk_mission_006_assimilation() -> None:
    report = run_mission_006_calibration_assimilation()
    assert report.passed, report.failures
