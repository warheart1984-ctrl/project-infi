"""Tests for invariant_engine_organ."""

from __future__ import annotations

from src.invariant_engine_organ import (
    MODULE_ID,
    build_invariant_engine_status,
    compare_nova_runtime_invariants,
)


def test_build_invariant_engine_status_companion_lane():
    status = build_invariant_engine_status(companion_lane="tiny_nova")
    assert status["invariant_engine_organ_version"] == "invariant_engine_organ.v1"
    assert status["module_id"] == MODULE_ID
    assert status["nova_runtime_consumer"] is True
    assert status["layer_invariant_count"] > 0
    assert status["read_only"] is True


def test_compare_nova_runtime_invariants_pipeline():
    comparison = compare_nova_runtime_invariants(
        companion_lane="small_nova",
        governed_pipeline={
            "realtime_event_cause_predictor": {
                "status": "bounded_inference",
                "runtime_context": "operator_runtime",
                "recommended_state": "observe",
                "cause_class": "steady_state",
                "advisory_only": True,
                "supporting_signals": [],
                "signal_count": 0,
                "phase_gate": {"decision": "ALLOW"},
            },
            "immune_protocol": {"response": "ALLOW"},
        },
    )
    assert comparison["layer_invariant_count"] > 0
    assert "realtime_invariant_status" in comparison
