"""Chat-path hard block when coherence_protocol is BLOCK."""

from __future__ import annotations

from unittest.mock import patch

from src.operator_cognition_coherence_fabric import (
    assert_coherence_allows_turn,
    coherence_hard_block_enabled,
    coherence_protocol_from_pipeline,
)


def test_coherence_protocol_from_pipeline_normalizes():
    protocol = coherence_protocol_from_pipeline(
        {"coherence_protocol": {"response": "block", "reason": "fabric misaligned"}}
    )
    assert protocol["response"] == "BLOCK"
    assert protocol["reason"] == "fabric misaligned"


def test_assert_coherence_allows_turn_blocks():
    result = assert_coherence_allows_turn(
        {"coherence_protocol": {"response": "BLOCK", "reason": "safety envelope halt"}}
    )
    assert not result.allowed
    assert "halt" in (result.reason or "")


def test_assert_coherence_allows_turn_respects_env_disable(monkeypatch):
    monkeypatch.setenv("AAIS_COHERENCE_HARD_BLOCK", "0")
    assert coherence_hard_block_enabled() is False
    result = assert_coherence_allows_turn(
        {"coherence_protocol": {"response": "BLOCK", "reason": "ignored"}}
    )
    assert result.allowed


def test_apply_coherence_guard_to_response_trace_blocks():
    from src.api import _apply_coherence_guard_to_response_trace

    trace = _apply_coherence_guard_to_response_trace(
        {
            "governed_pipeline": {
                "coherence_protocol": {
                    "response": "BLOCK",
                    "reason": "coherence fabric misaligned",
                }
            },
            "god_brain": {"summary": "test"},
        }
    )
    assert trace.get("blocked_by") == "coherence_fabric"
    assert trace.get("contract") == "coherence_blocked"


def test_hydrate_context_returns_block_metadata(monkeypatch):
    from types import SimpleNamespace

    from src.api import _apply_coherence_guard_to_response_trace

    session = SimpleNamespace(metadata={})
    pipeline = {
        "coherence_protocol": {"response": "BLOCK", "reason": "test block"},
        "pipeline_id": "gdp_test",
    }
    trace = _apply_coherence_guard_to_response_trace(
        {"governed_pipeline": pipeline, "god_brain": {"summary": "x"}}
    )
    assert trace["blocked_by"] == "coherence_fabric"

    with patch(
        "src.operator_cognition_coherence_fabric.build_coherence_fabric_status",
        return_value={
            "fabric_genes_aligned": False,
            "envelope_governance_modes": [
                {"envelope_id": "safety_envelope", "governance_mode": "strict"}
            ],
        },
    ):
        blocked = assert_coherence_allows_turn(pipeline)
    assert not blocked.allowed
