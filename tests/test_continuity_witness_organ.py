"""Tests for continuity_witness_organ."""

from __future__ import annotations

from src.continuity_witness_organ import build_continuity_witness_status


def test_build_continuity_witness_status():
    status = build_continuity_witness_status()
    assert status["continuity_witness_organ_version"] == "continuity_witness_organ.v1"
    assert status["module_id"] == "AAIS-CW-01"
    assert status["drift_band"] in {"nominal", "watch", "drifting", "critical", "idle"}
    assert status["read_only"] is True


def test_build_continuity_witness_status_coherence_boundary():
    status = build_continuity_witness_status(
        governed_pipeline={
            "coherence_protocol": {"response": "BLOCK", "reason": "fabric misaligned"},
        }
    )
    assert status["coherence_boundary"] is True
    assert status["coherence_protocol_response"] == "block"
