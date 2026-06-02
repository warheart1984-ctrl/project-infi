"""Tests for reflection_runtime_organ."""

from __future__ import annotations

from src.reflection_runtime_organ import build_reflection_runtime_status


def test_build_reflection_runtime_status():
    status = build_reflection_runtime_status()
    assert status["reflection_runtime_organ_version"] == "reflection_runtime_organ.v1"
    assert status["runtime_id"] == "cognitive.reflection"
    assert status["stages"] == ["expect", "compare", "learn", "adjust"]
    assert status["read_only"] is True
