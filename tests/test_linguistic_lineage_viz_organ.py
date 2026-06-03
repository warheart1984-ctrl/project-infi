"""Tests for linguistic_lineage_viz_organ."""

from __future__ import annotations

from src.linguistic_lineage_viz_organ import build_linguistic_lineage_viz_status


def test_build_status():
    status = build_linguistic_lineage_viz_status()
    assert status["linguistic_lineage_viz_organ_version"] == "linguistic_lineage_viz_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
