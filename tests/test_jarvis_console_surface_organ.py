"""Tests for jarvis_console_surface_organ."""

from __future__ import annotations

from src.jarvis_console_surface_organ import build_jarvis_console_surface_status


def test_build_status():
    status = build_jarvis_console_surface_status()
    assert status["jarvis_console_surface_organ_version"] == "jarvis_console_surface_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

