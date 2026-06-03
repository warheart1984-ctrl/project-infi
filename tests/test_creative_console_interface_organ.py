"""Tests for creative_console_interface_organ."""

from __future__ import annotations

from src.creative_console_interface_organ import build_creative_console_interface_status


def test_build_status():
    status = build_creative_console_interface_status()
    assert status["creative_console_interface_organ_version"] == "creative_console_interface_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
