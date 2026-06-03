"""Tests for speaking_runtime_organ."""

from __future__ import annotations

from src.speaking_runtime_organ import build_speaking_runtime_status


def test_build_status():
    status = build_speaking_runtime_status()
    assert status["speaking_runtime_organ_version"] == "speaking_runtime_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

