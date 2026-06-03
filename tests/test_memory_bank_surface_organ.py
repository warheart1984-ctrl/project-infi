"""Tests for memory_bank_surface_organ."""

from __future__ import annotations

from src.memory_bank_surface_organ import build_memory_bank_surface_status


def test_build_status():
    status = build_memory_bank_surface_status()
    assert status["memory_bank_surface_organ_version"] == "memory_bank_surface_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

