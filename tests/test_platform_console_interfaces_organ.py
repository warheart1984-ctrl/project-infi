"""Tests for platform_console_interfaces_organ."""

from __future__ import annotations

from src.platform_console_interfaces_organ import build_platform_console_interfaces_status


def test_build_status():
    status = build_platform_console_interfaces_status()
    assert status["platform_console_interfaces_organ_version"] == "platform_console_interfaces_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
