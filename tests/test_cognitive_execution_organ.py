"""Tests for cognitive_execution_organ."""

from __future__ import annotations

from src.cognitive_execution_organ import build_cognitive_execution_status


def test_build_status():
    status = build_cognitive_execution_status()
    assert status["cognitive_execution_organ_version"] == "cognitive_execution_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("patch_execution_depth") is False

