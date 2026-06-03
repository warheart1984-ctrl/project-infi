"""Tests for dashboard_surface_organ."""

from __future__ import annotations

from src.dashboard_surface_organ import build_dashboard_surface_status


def test_build_status():
    status = build_dashboard_surface_status()
    assert status["dashboard_surface_organ_version"] == "dashboard_surface_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

