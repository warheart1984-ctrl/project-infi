"""Tests for nova_landing_surface_organ."""

from __future__ import annotations

from src.nova_landing_surface_organ import build_nova_landing_surface_status


def test_build_status():
    status = build_nova_landing_surface_status()
    assert status["nova_landing_surface_organ_version"] == "nova_landing_surface_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

