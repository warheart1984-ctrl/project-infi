"""Invariant Engine Organ — read-only Nova runtime consumer attestation."""

# Mythic: Invariant Engine Organ
# Engineering: InvariantEngineEngine
from __future__ import annotations

from typing import Any

from src.invariant_engine import InvariantEngine
from src.super_nova_anchor import build_default_super_nova_layer_invariants

MODULE_ID = "aais.invariant_engine"
MODULE_ORGAN_VERSION = "invariant_engine_organ.v1"


def compare_nova_runtime_invariants(
    *,
    companion_lane: str | None = None,
    governed_pipeline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read-only Nova anchor and realtime invariant comparison (no escalation)."""
    layers = build_default_super_nova_layer_invariants()
    comparison: dict[str, Any] = {
        "layer_invariant_count": len(layers),
        "companion_lane": str(companion_lane or "")[:64],
        "status": "observed",
        "advisory_only": True,
    }
    pipeline = dict(governed_pipeline or {})
    prediction = dict(pipeline.get("realtime_event_cause_predictor") or {})
    if prediction:
        event = {
            "runtime_context": str(prediction.get("runtime_context") or "operator_runtime"),
            "signals": list(prediction.get("supporting_signals") or []),
            "signal_count": int(prediction.get("signal_count") or 0),
            "immune_response": str(
                (pipeline.get("immune_protocol") or {}).get("response") or "ALLOW"
            ).upper(),
            "validation": dict((pipeline.get("validation") or {})),
        }
        result = InvariantEngine.validate_realtime_event_prediction(event, prediction)
        comparison["realtime_invariant_status"] = str(result.get("status") or "unknown")[:32]
        comparison["realtime_invariant_allows"] = bool(result.get("allows"))
    return comparison


def build_invariant_engine_status(
    *,
    companion_lane: str | None = None,
    governed_pipeline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bounded invariant engine snapshot for governance surfaces."""
    comparison = compare_nova_runtime_invariants(
        companion_lane=companion_lane,
        governed_pipeline=governed_pipeline,
    )
    layer_count = int(comparison.get("layer_invariant_count") or 0)
    has_lane = bool(str(comparison.get("companion_lane") or "").strip())
    has_realtime = "realtime_invariant_status" in comparison
    nova_consumer = layer_count > 0 and (has_lane or has_realtime)
    bridge_posture = "idle"
    if has_realtime:
        bridge_posture = (
            "pass" if comparison.get("realtime_invariant_allows") else "advisory_fail"
        )
    elif has_lane:
        bridge_posture = "anchor_observed"
    return {
        "invariant_engine_organ_version": MODULE_ORGAN_VERSION,
        "module_id": MODULE_ID,
        "nova_runtime_consumer": nova_consumer,
        "bridge_validation_posture": bridge_posture[:32],
        "layer_invariant_count": layer_count,
        "last_comparison_status": str(comparison.get("status") or "idle")[:32],
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
