"""Tests for memory_runtime_organ."""

from __future__ import annotations

from src.memory_runtime_organ import build_memory_runtime_status


def test_build_memory_runtime_status():
    status = build_memory_runtime_status()
    assert status["memory_runtime_organ_version"] == "memory_runtime_organ.v1"
    assert status["runtime_id"] == "cognitive.memory"
    assert len(status["stages"]) >= 1
    assert status["read_only"] is True
