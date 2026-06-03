"""Tests for naming_genome_organ."""

from __future__ import annotations

from src.naming_genome_organ import build_naming_genome_status


def test_build_status():
    status = build_naming_genome_status()
    assert status["naming_genome_organ_version"] == "naming_genome_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
