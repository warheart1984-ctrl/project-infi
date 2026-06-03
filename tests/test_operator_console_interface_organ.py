"""Tests for operator_console_interface_organ."""

from __future__ import annotations

from src.operator_console_interface_organ import build_operator_console_interface_status


def test_build_status():
    status = build_operator_console_interface_status()
    assert status["operator_console_interface_organ_version"] == "operator_console_interface_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
