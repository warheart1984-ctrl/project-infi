"""Tests for aais_composed_runtime_organ."""

from __future__ import annotations

from src.aais_composed_runtime_organ import build_aais_composed_runtime_status


def test_build_status():
    status = build_aais_composed_runtime_status()
    assert status["aais_composed_runtime_organ_version"] == "aais_composed_runtime_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

