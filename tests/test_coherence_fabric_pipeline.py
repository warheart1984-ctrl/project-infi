"""Pipeline integration with Alt-7.1 coherence guard."""

from __future__ import annotations

from unittest.mock import patch

from src.governed_direct_pipeline import build_governed_turn_pipeline


def _healthy_coherence_status() -> dict:
    return {
        "fabric_genes_aligned": True,
        "envelope_governance_modes": [
            {"envelope_id": "safety_envelope", "governance_mode": "strict"},
        ],
    }


def test_pipeline_coherence_allow_when_aligned():
    with patch(
        "src.operator_cognition_coherence_fabric.build_coherence_fabric_status",
        return_value=_healthy_coherence_status(),
    ):
        trace = build_governed_turn_pipeline(response_mode="fast")
    assert trace.get("coherence_protocol", {}).get("response") == "ALLOW"


def test_pipeline_coherence_block_when_safety_halt():
    with patch(
        "src.operator_cognition_coherence_fabric.build_coherence_fabric_status",
        return_value={
            "fabric_genes_aligned": True,
            "envelope_governance_modes": [
                {"envelope_id": "safety_envelope", "governance_mode": "halt"},
            ],
        },
    ):
        trace = build_governed_turn_pipeline(response_mode="fast")
    assert trace.get("coherence_protocol", {}).get("response") == "BLOCK"


def test_assert_coherence_allows_turn_from_live_pipeline():
    from src.operator_cognition_coherence_fabric import assert_coherence_allows_turn

    with patch(
        "src.operator_cognition_coherence_fabric.build_coherence_fabric_status",
        return_value=_healthy_coherence_status(),
    ):
        trace = build_governed_turn_pipeline(response_mode="fast")
    assert trace.get("coherence_protocol", {}).get("response") == "ALLOW"
    assert assert_coherence_allows_turn(trace).allowed


def test_pipeline_coherence_block_when_fabric_misaligned():
    with patch(
        "src.operator_cognition_coherence_fabric.build_coherence_fabric_status",
        return_value={
            "fabric_genes_aligned": False,
            "envelope_governance_modes": [
                {"envelope_id": "safety_envelope", "governance_mode": "strict"},
            ],
        },
    ):
        trace = build_governed_turn_pipeline(response_mode="fast")
    protocol = trace.get("coherence_protocol") or {}
    assert protocol.get("response") == "BLOCK"
    assert "misaligned" in str(protocol.get("reason") or "").lower()
