"""Realtime Event Cause Predictor Organ — read-only live producer attestation."""

# Mythic: Realtime Event Cause Predictor Organ
# Engineering: RealtimeEventCausePredictorEngine
from __future__ import annotations

from typing import Any

from src.realtime_event_cause_predictor import (
    MODULE_ID,
    PREDICTOR_COMPONENT_ID,
    validate_interpreted_event_state,
)
from src.phase_gate import ComponentNotRegisteredError, get_component

MODULE_ORGAN_VERSION = "realtime_event_cause_predictor_organ.v1"


def _predictor_phase_registered() -> bool:
    try:
        get_component(PREDICTOR_COMPONENT_ID)
        return True
    except ComponentNotRegisteredError:
        return False


def _pipeline_producer_valid(governed_pipeline: dict[str, Any] | None) -> bool:
    if not isinstance(governed_pipeline, dict) or not governed_pipeline:
        return False
    prediction = dict(governed_pipeline.get("realtime_event_cause_predictor") or {})
    if not prediction:
        return False
    validation = dict((governed_pipeline.get("validation") or {}))
    if validation.get("realtime_event_cause_predictor_valid") is True:
        return True
    checks = validate_interpreted_event_state(prediction)
    return all(value for value in checks.values() if isinstance(value, bool))


def build_realtime_predictor_status(
    *,
    governed_pipeline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bounded predictor snapshot with live runtime producer attestation."""
    pipeline = dict(governed_pipeline or {})
    prediction = dict(pipeline.get("realtime_event_cause_predictor") or {})
    live_producer = _pipeline_producer_valid(pipeline if pipeline else None)
    status = str(prediction.get("status") or "idle")[:64]
    recommended = str(prediction.get("recommended_state") or "observe")[:32]
    cause_class = str(prediction.get("cause_class") or "insufficient_signal")[:64]
    summary = f"{status}:{recommended}:{cause_class}"[:128]
    return {
        "realtime_event_cause_predictor_organ_version": MODULE_ORGAN_VERSION,
        "module_id": MODULE_ID,
        "phase_registered": _predictor_phase_registered(),
        "live_runtime_producer": live_producer,
        "last_rt_summary": summary,
        "recommended_state": recommended,
        "cause_class": cause_class,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
