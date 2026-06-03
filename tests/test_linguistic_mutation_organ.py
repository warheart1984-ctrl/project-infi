"""Tests for linguistic_mutation_organ."""

from __future__ import annotations

from src.linguistic_mutation_organ import build_linguistic_mutation_status


def test_build_status():
    status = build_linguistic_mutation_status()
    assert status["linguistic_mutation_organ_version"] == "linguistic_mutation_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
