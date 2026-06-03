"""Tests for coherence_projection_organ."""

from __future__ import annotations

from src.coherence_projection_organ import build_coherence_projection_status


def test_build_status():
    status = build_coherence_projection_status()
    assert status["coherence_projection_organ_version"] == "coherence_projection_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("exports_chain_of_thought") is False
    assert status.get("exports_bounded_state") is True

