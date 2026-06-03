"""Tests for planning_organ."""

from __future__ import annotations

from src.planning_organ import build_planning_status


def test_build_status():
    status = build_planning_status()
    assert status["planning_organ_version"] == "planning_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

