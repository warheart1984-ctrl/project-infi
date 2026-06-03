"""Tests for forensic_triangulation_organ."""

from __future__ import annotations

from src.forensic_triangulation_organ import build_forensic_triangulation_status


def test_build_status():
    status = build_forensic_triangulation_status()
    assert status["forensic_triangulation_organ_version"] == "forensic_triangulation_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
