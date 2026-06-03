"""Tests for system_guard_organ."""

from __future__ import annotations

from src.system_guard_organ import build_system_guard_status


def test_build_status():
    status = build_system_guard_status()
    assert status["system_guard_organ_version"] == "system_guard_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

