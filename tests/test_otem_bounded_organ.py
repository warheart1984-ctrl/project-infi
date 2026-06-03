"""Tests for otem_bounded_organ."""

from __future__ import annotations

from src.otem_bounded_organ import build_otem_bounded_status


def test_build_status():
    status = build_otem_bounded_status()
    assert status["otem_bounded_organ_version"] == "otem_bounded_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
