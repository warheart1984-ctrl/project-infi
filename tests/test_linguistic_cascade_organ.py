"""Tests for linguistic_cascade_organ."""

from __future__ import annotations

from src.linguistic_cascade_organ import build_linguistic_cascade_status


def test_build_status():
    status = build_linguistic_cascade_status()
    assert status["linguistic_cascade_organ_version"] == "linguistic_cascade_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
