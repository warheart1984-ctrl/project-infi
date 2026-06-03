"""Tests for orchestration_spine_organ."""

from __future__ import annotations

from src.orchestration_spine_organ import build_orchestration_spine_status


def test_build_status():
    status = build_orchestration_spine_status()
    assert status["orchestration_spine_organ_version"] == "orchestration_spine_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
