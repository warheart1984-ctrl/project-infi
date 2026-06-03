"""Tests for anti_drift_organ."""

from __future__ import annotations

from src.anti_drift_organ import build_anti_drift_status


def test_build_status():
    status = build_anti_drift_status()
    assert status["anti_drift_organ_version"] == "anti_drift_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

