"""Tests for v8_runtime_organ."""

from __future__ import annotations

from src.v8_runtime_organ import build_v8_runtime_status


def test_build_status():
    status = build_v8_runtime_status()
    assert status["v8_runtime_organ_version"] == "v8_runtime_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
