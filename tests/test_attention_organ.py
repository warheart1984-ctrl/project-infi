"""Tests for attention_organ."""

from __future__ import annotations

from src.attention_organ import build_attention_status


def test_build_status():
    status = build_attention_status()
    assert status["attention_organ_version"] == "attention_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

