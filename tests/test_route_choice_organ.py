"""Tests for route_choice_organ."""

from __future__ import annotations

from src.route_choice_organ import build_route_choice_status


def test_build_status():
    status = build_route_choice_status()
    assert status["route_choice_organ_version"] == "route_choice_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("model_route_count", 0) >= 1
    assert status.get("routing_read_only") is True

