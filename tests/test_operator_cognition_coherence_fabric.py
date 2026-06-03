"""Tests for operator_cognition_coherence_fabric."""

from __future__ import annotations

from pathlib import Path

from src.operator_cognition_coherence_fabric import build_coherence_fabric_status


def test_build_coherence_fabric_status_schema_fields():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert status["operator_cognition_coherence_fabric_version"] == (
        "operator_cognition_coherence_fabric.v1.2"
    )
    assert status["read_only"] is True
    assert status["authority_lane"] == "operator"
    assert status["resolved_lane"]
    assert "fabric_genes_aligned" in status
    assert status["lane_awakened"] is True


def test_envelope_governance_modes():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    modes = {item["envelope_id"]: item["governance_mode"] for item in status["envelope_governance_modes"]}
    assert set(modes) == {
        "capability_service_bridge",
        "governed_direct_pipeline",
        "jarvis_memory_board",
        "safety_envelope",
    }
    assert modes["capability_service_bridge"] in {"strict", "assist", "experimental"}


def test_fabric_genes_aligned_in_healthy_repo():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert status["fabric_genes_aligned"] is True


def test_lane_coherence_with_profile_authority():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert status["authority_lane"] == "operator"
    assert status["resolved_lane"] == "operator"


def test_v12_health_fields_present():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert "coherence_pipeline_allowed" in status
    assert "safety_envelope_halt" in status


def test_runtime_posture_includes_alt5_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("runtime_posture") or []}
    assert organs == {"reflection_runtime_organ", "memory_runtime_organ"}


def test_evaluate_pipeline_coherence_blocks_misaligned():
    from src.operator_cognition_coherence_fabric import evaluate_pipeline_coherence

    result = evaluate_pipeline_coherence(fabric_genes_aligned=False, safety_halt=False)
    assert not result.allowed
    assert result.reason == "coherence fabric misaligned"


def test_live_pipeline_trace_in_snapshot():
    trace = {
        "pipeline_id": "gdp_live",
        "version": "1",
        "active_lane": "direct_cognitive",
        "coherence_protocol": {"response": "ALLOW"},
        "realtime_signal_feed": {"risk_level": "low"},
        "immune_protocol": {"response": "ALLOW"},
        "forward_packets": [],
        "service_packets": [],
        "return_packets": [],
    }
    status = build_coherence_fabric_status(
        root=Path(__file__).resolve().parents[1],
        pipeline_trace=trace,
    )
    assert status.get("last_coherence_response") == "ALLOW"


def test_evaluate_pipeline_coherence_allows_aligned():
    from src.operator_cognition_coherence_fabric import evaluate_pipeline_coherence

    result = evaluate_pipeline_coherence(fabric_genes_aligned=True, safety_halt=False)
    assert result.allowed


def test_evaluate_bridge_coherence_blocks_misaligned_fabric():
    from src.adaptive_lane_organ import LaneResolution
    from src.operator_cognition_coherence_fabric import evaluate_bridge_coherence

    result = evaluate_bridge_coherence(
        capability_id="recipe_module",
        lane_resolution=LaneResolution(lane_id="operator", weight=1.0, capabilities=()),
        bridge_governance_mode="strict",
        fabric_genes_aligned=False,
        safety_halt=False,
    )
    assert not result.allowed
    assert result.reason == "coherence fabric misaligned"


def test_evaluate_bridge_coherence_blocks_policy_cap_non_strict():
    from src.adaptive_lane_organ import LaneResolution
    from src.operator_cognition_coherence_fabric import evaluate_bridge_coherence

    result = evaluate_bridge_coherence(
        capability_id="approve_policy_changes",
        lane_resolution=LaneResolution(
            lane_id="operator",
            weight=1.0,
            capabilities=("approve_policy_changes",),
        ),
        bridge_governance_mode="assist",
        fabric_genes_aligned=True,
        safety_halt=False,
    )
    assert not result.allowed
    assert "strict" in (result.reason or "")
