"""Tests for launcher_organ."""

from __future__ import annotations

from src.launcher_organ import build_launcher_status


def test_build_status():
    status = build_launcher_status()
    assert status["launcher_organ_version"] == "launcher_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

