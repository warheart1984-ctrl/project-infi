"""Tests for v9_runtime_organ."""

from __future__ import annotations

from src.v9_runtime_organ import build_v9_runtime_status


def test_build_status():
    status = build_v9_runtime_status()
    assert status["v9_runtime_organ_version"] == "v9_runtime_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
