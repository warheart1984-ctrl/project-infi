"""Tests for forge_eval_organ."""

from __future__ import annotations

from src.forge_eval_organ import build_forge_eval_status


def test_build_status():
    status = build_forge_eval_status()
    assert status["forge_eval_organ_version"] == "forge_eval_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

