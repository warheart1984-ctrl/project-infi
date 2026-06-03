"""Tests for capability_module_organ."""

from __future__ import annotations

from src.capability_module_organ import build_capability_module_status


def test_build_status():
    status = build_capability_module_status()
    assert status["capability_module_organ_version"] == "capability_module_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
