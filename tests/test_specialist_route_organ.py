"""Tests for specialist_route_organ."""

from __future__ import annotations

from src.specialist_route_organ import build_specialist_route_status


def test_build_status():
    status = build_specialist_route_status()
    assert status["specialist_route_organ_version"] == "specialist_route_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

