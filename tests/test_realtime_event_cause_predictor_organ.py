"""Tests for realtime_event_cause_predictor_organ."""

from __future__ import annotations

from src.realtime_event_cause_predictor import MODULE_ID
from src.realtime_event_cause_predictor_organ import build_realtime_predictor_status


def test_build_realtime_predictor_status_idle():
    status = build_realtime_predictor_status()
    assert status["realtime_event_cause_predictor_organ_version"] == (
        "realtime_event_cause_predictor_organ.v1"
    )
    assert status["module_id"] == MODULE_ID
    assert status["live_runtime_producer"] is False
    assert status["read_only"] is True


def test_build_realtime_predictor_status_live_producer():
    status = build_realtime_predictor_status(
        governed_pipeline={
            "realtime_event_cause_predictor": {
                "status": "bounded_inference",
                "runtime_context": "operator_runtime",
                "recommended_state": "observe",
                "cause_class": "steady_state",
                "advisory_only": True,
                "supporting_signals": ["sig"],
                "signal_count": 1,
                "phase_gate": {"decision": "ALLOW"},
            },
            "validation": {"realtime_event_cause_predictor_valid": True},
        }
    )
    assert status["live_runtime_producer"] is True
