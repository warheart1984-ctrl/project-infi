"""Lineage reconstruction helpers."""

from __future__ import annotations

from typing import Any


def reconstruct_from_m005() -> dict[str, Any]:
    from src.crk1.mission_005_calibration_lineage_stress import run_mission_005_calibration_lineage_stress

    return run_mission_005_calibration_lineage_stress().to_dict()
