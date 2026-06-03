"""Tests for mythic_engineering_translator_organ."""

from __future__ import annotations

from src.mythic_engineering_translator_organ import build_mythic_engineering_translator_status


def test_build_status():
    status = build_mythic_engineering_translator_status()
    assert status["mythic_engineering_translator_organ_version"] == "mythic_engineering_translator_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
