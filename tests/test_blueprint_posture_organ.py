"""Tests for blueprint_posture_organ."""

from __future__ import annotations

from src.blueprint_posture_organ import build_blueprint_posture_status


def test_build_status():
    status = build_blueprint_posture_status()
    assert status["blueprint_posture_organ_version"] == "blueprint_posture_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
