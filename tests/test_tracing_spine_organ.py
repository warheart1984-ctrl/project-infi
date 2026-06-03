"""Tests for tracing_spine_organ."""

from __future__ import annotations

from src.tracing_spine_organ import build_tracing_spine_status


def test_build_status():
    status = build_tracing_spine_status()
    assert status["tracing_spine_organ_version"] == "tracing_spine_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
