"""Tests for ui_vision_organ."""

from __future__ import annotations

from src.ui_vision_organ import build_ui_vision_status


def test_build_status():
    status = build_ui_vision_status()
    assert status["ui_vision_organ_version"] == "ui_vision_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

