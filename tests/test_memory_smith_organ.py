"""Tests for memory_smith_organ."""

from __future__ import annotations

from src.memory_smith_organ import build_memory_smith_status


def test_build_status():
    status = build_memory_smith_status()
    assert status["memory_smith_organ_version"] == "memory_smith_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
