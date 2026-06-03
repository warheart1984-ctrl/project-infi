"""Tests for aris_boundary_organ."""

from __future__ import annotations

from src.aris_boundary_organ import build_aris_boundary_status


def test_build_status():
    status = build_aris_boundary_status()
    assert status["aris_boundary_organ_version"] == "aris_boundary_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
