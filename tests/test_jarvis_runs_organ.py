"""Tests for jarvis_runs_organ."""

from __future__ import annotations

from src.jarvis_runs_organ import build_jarvis_runs_status


def test_build_status():
    status = build_jarvis_runs_status()
    assert status["jarvis_runs_organ_version"] == "jarvis_runs_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
