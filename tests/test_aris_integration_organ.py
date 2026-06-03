"""Tests for aris_integration_organ."""

from __future__ import annotations

from src.aris_integration_organ import build_aris_integration_status


def test_build_status():
    status = build_aris_integration_status()
    assert status["aris_integration_organ_version"] == "aris_integration_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

