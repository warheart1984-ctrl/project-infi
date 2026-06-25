"""Integration tests for subsystem MVP + governed wave."""

from __future__ import annotations

import os


def test_memory_path_registry_aligned_when_slots_full():
    from src.memory_path_registry import memory_paths_aligned

    assert memory_paths_aligned(board_slots_installed=4, board_slots_total=4) is True
    assert memory_paths_aligned(board_slots_installed=1, board_slots_total=4) is False


def test_memory_path_governance_organ_reports_alignment():
    from src.memory_path_governance_organ import build_memory_path_governance_status

    status = build_memory_path_governance_status()
    assert "memory_paths_aligned" in status
    assert isinstance(status["board_governed_paths"], list)


def test_module_entry_gate_status():
    from src.module_entry_gate import build_module_entry_gate_status

    status = build_module_entry_gate_status()
    assert status["total_components"] >= 1
    assert "entry_coverage_ratio" in status


def test_universal_bridge_attached_on_jarvis_operator():
    from src.capability_bridge_universal import universal_bridge_enforced
    from src.jarvis_operator import jarvis_operator

    assert universal_bridge_enforced(jarvis_operator.capability_bridge) is True


def test_capability_module_organ_universal_when_bridge_attached():
    from src.capability_module_organ import build_capability_module_status

    status = build_capability_module_status()
    assert status["universal_bridge_enforced"] is True
    assert status["bridge_gap_paths"] == []


def test_pipeline_transport_flag():
    from src.governed_direct_pipeline import build_governed_turn_pipeline, pipeline_as_transport_enabled

    os.environ.pop("AAIS_PIPELINE_AS_TRANSPORT", None)
    assert pipeline_as_transport_enabled() is False
    os.environ["AAIS_PIPELINE_AS_TRANSPORT"] = "1"
    assert pipeline_as_transport_enabled() is True
    pipeline = build_governed_turn_pipeline(response_mode="fast", runtime_context="test_harness")
    assert pipeline.get("transport_substrate") is True
    os.environ.pop("AAIS_PIPELINE_AS_TRANSPORT", None)


def test_governed_pipeline_packet_shape():
    from src.governed_direct_pipeline import build_governed_turn_pipeline

    pipeline = build_governed_turn_pipeline(response_mode="fast", runtime_context="test_harness")
    assert pipeline.get("forward_packets")
    assert pipeline.get("return_packets")
    assert pipeline["validation"]["uniform_packet_shape"] is True


def test_perception_gateway_routes_document_vision():
    from src.perception_gateway_organ import PERCEPTION_CAPABILITIES, route_perception_entry

    assert "document_vision" in PERCEPTION_CAPABILITIES
    blocked = route_perception_entry("document_vision", {})
    assert blocked.get("ok") is False


def test_realtime_feed_adapter_collects():
    from src.realtime_feed_adapter import get_realtime_feed_adapter

    events = get_realtime_feed_adapter().collect(limit=4)
    assert isinstance(events, list)


def test_otem_execution_substrate_workflow():
    from src.otem.execution import get_otem_execution_substrate

    substrate = get_otem_execution_substrate()
    proposal = substrate.create_proposal({"summary": "test"}, runtime_context="test_harness")
    approved = substrate.approve(proposal["workflow_id"], runtime_context="test_harness")
    assert approved["operator_approved"] is True
    applied = substrate.apply(proposal["workflow_id"], runtime_context="test_harness")
    assert applied["stage"] == "ledger_record"


def test_aris_client_embedded_mode():
    from src.aris_service_client import build_aris_client_status, evaluate_aris_admission

    os.environ.pop("ARIS_MODE", None)
    status = build_aris_client_status()
    assert status["mode"] == "embedded"
    result = evaluate_aris_admission(details={"pattern_share_mode": "local_only"})
    assert result.get("runtime_profile")


def test_dreamspace_organ_status():
    from src.dreamspace_organ import build_dreamspace_organ_status

    status = build_dreamspace_organ_status()
    assert status["opt_in_required"] is True
    assert status["governed_activation"] is True


def test_media_processor_organ_status():
    from src.media_processor_organ import build_media_processor_organ_status

    status = build_media_processor_organ_status()
    assert "audio_analyze" in status["media_capabilities"]


def test_beatbox_speakers_standalone_lane_flags():
    from src.beatbox_lane_organ import build_beatbox_lane_status
    from src.speakers_lane_organ import build_speakers_lane_status

    assert build_beatbox_lane_status()["standalone_lane_admitted"] is True
    assert build_speakers_lane_status()["standalone_lane_admitted"] is True
