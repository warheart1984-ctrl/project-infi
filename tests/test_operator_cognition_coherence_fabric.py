"""Tests for operator_cognition_coherence_fabric."""

from __future__ import annotations

from pathlib import Path

from src.operator_cognition_coherence_fabric import build_coherence_fabric_status


def test_build_coherence_fabric_status_schema_fields():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert status["operator_cognition_coherence_fabric_version"] == (
        "operator_cognition_coherence_fabric.v1.17"
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


def test_mind_posture_includes_alt8_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("mind_posture") or []}
    assert organs == {
        "continuity_witness_organ",
        "narrative_continuity_organ",
        "intent_agency_organ",
    }
    assert status.get("mind_planes_aligned") is True


def test_infrastructure_posture_includes_alt9_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("infrastructure_posture") or []}
    assert organs == {
        "phase_gate_organ",
        "realtime_event_cause_predictor_organ",
        "invariant_engine_organ",
    }


def test_memory_governance_posture_includes_alt10_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("memory_governance_posture") or []}
    assert organs == {
        "verification_gate_organ",
        "memory_path_governance_organ",
        "knowledge_authority_organ",
    }
    assert status.get("memory_paths_aligned") is True


def test_forensics_posture_includes_alt10_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("forensics_posture") or []}
    assert organs == {
        "scorpion_bridge_organ",
        "mechanic_handoff_organ",
        "forensic_triangulation_organ",
    }
    assert status.get("forensics_handoff_aligned") is True


def test_immune_observe_posture_includes_alt10_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("immune_observe_posture") or []}
    assert organs == {
        "immune_observe_organ",
        "policy_gate_organ",
        "predictor_immune_bridge_organ",
    }


def test_immune_observe_aligned_with_pipeline():
    trace = {
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
        "validation": {"realtime_event_cause_predictor_valid": True},
    }
    status = build_coherence_fabric_status(
        root=Path(__file__).resolve().parents[1],
        pipeline_trace=trace,
    )
    assert status.get("immune_observe_aligned") is True


def test_infrastructure_substrate_aligned_with_pipeline():
    trace = {
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
        "validation": {"realtime_event_cause_predictor_valid": True},
    }
    status = build_coherence_fabric_status(
        root=Path(__file__).resolve().parents[1],
        pipeline_trace=trace,
    )
    assert status.get("infrastructure_substrate_aligned") is True


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


def test_authority_trace_posture_includes_alt11_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("authority_trace_posture") or []}
    assert organs == {
        "cognitive_bridge_organ",
        "governed_event_chain_organ",
        "tracing_spine_organ",
    }
    assert status.get("authority_trace_aligned") is True


def test_mission_boundary_posture_includes_alt11_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("mission_boundary_posture") or []}
    assert organs == {
        "mission_board_organ",
        "aris_boundary_organ",
        "capability_module_organ",
    }
    assert status.get("mission_boundary_aligned") is True


def test_coding_posture_includes_alt11_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("coding_posture") or []}
    assert organs == {
        "patchforge_organ",
        "change_scope_organ",
        "patch_verification_organ",
    }
    assert status.get("coding_stack_aligned") is True


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


def test_otem_lane_posture_includes_alt12_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("otem_lane_posture") or []}
    assert organs == {
        "otem_bounded_organ",
        "direct_challenge_organ",
        "orchestration_spine_organ",
    }
    assert status.get("otem_lane_aligned") is True


def test_predictive_lane_posture_includes_alt12_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("predictive_lane_posture") or []}
    assert organs == {
        "operator_health_sentinel_organ",
        "governed_realtime_lane_organ",
        "v8_runtime_organ",
    }
    assert status.get("predictive_lane_aligned") is True


def test_execution_depth_posture_includes_alt12_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("execution_depth_posture") or []}
    assert organs == {
        "patch_apply_organ",
        "patch_execution_preview_organ",
        "run_ledger_organ",
    }
    assert status.get("execution_depth_aligned") is True


def test_constitutional_creative_posture_includes_alt13_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("constitutional_creative_posture") or []}
    assert organs == {
        "ul_lineage_console_organ",
        "recipe_module_organ",
        "imagine_generator_organ",
        "human_voice_extraction_organ",
        "narrative_trust_pack_organ",
    }
    assert status.get("constitutional_creative_aligned") is True


def test_story_chain_posture_includes_alt13_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("story_chain_posture") or []}
    assert organs == {
        "story_forge_lane_organ",
        "beatbox_lane_organ",
        "speakers_lane_organ",
    }
    assert status.get("story_chain_aligned") is True
    assert status.get("creative_chain_aligned") is True


def test_module_governance_posture_includes_alt13_organ():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("module_governance_posture") or []}
    assert organs == {"module_governance_organ"}
    assert status.get("module_governance_aligned") is True


def test_alt16_factory_kinetic_planes_at_v111():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert len(status.get("factory_fabrication_posture") or []) == 3
    assert len(status.get("contractor_lane_posture") or []) == 3
    assert len(status.get("kinetic_shell_posture") or []) == 3
    assert status.get("factory_fabrication_aligned") is True
    assert status.get("contractor_lanes_aligned") is True
    assert status.get("kinetic_shell_aligned") is True
    assert status.get("factory_kinetic_aligned") is True


def test_alt19_operator_product_shell_planes_at_v114():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert status["operator_cognition_coherence_fabric_version"] == (
        "operator_cognition_coherence_fabric.v1.17"
    )
    assert len(status.get("product_shell_posture") or []) == 3
    assert len(status.get("operator_surface_posture") or []) == 4
    assert len(status.get("composed_runtime_posture") or []) == 2
    assert status.get("product_shell_aligned") is True
    assert status.get("operator_surface_aligned") is True
    assert status.get("composed_runtime_aligned") is True
    assert status.get("operator_product_shell_aligned") is True


def test_alt20_operator_workspace_interfaces_layers_at_v115():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert len(status.get("workspace_memory_layer") or []) == 3
    assert len(status.get("hygiene_blueprint_layer") or []) == 3
    assert len(status.get("extended_operator_interface_layer") or []) == 3
    assert status.get("workspace_memory_aligned") is True
    assert status.get("hygiene_blueprint_aligned") is True
    assert status.get("extended_operator_interface_aligned") is True
    assert status.get("operator_workspace_interfaces_aligned") is True


def test_alt21_creative_runtime_v9_v10_layers_at_v116():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert status["operator_cognition_coherence_fabric_version"] == (
        "operator_cognition_coherence_fabric.v1.17"
    )
    assert len(status.get("creative_core_layer") or []) == 3
    assert len(status.get("v9_creative_layer") or []) == 3
    assert len(status.get("v10_creative_layer") or []) == 3
    assert status.get("creative_core_aligned") is True
    assert status.get("v9_creative_aligned") is True
    assert status.get("v10_creative_aligned") is True
    assert status.get("creative_runtime_v9_v10_aligned") is True


def test_alt22_meta_linguistic_layers_at_v117():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert status["operator_cognition_coherence_fabric_version"] == (
        "operator_cognition_coherence_fabric.v1.17"
    )
    assert len(status.get("naming_protocol_layer") or []) == 3
    assert len(status.get("linguistic_mutation_layer") or []) == 3
    assert len(status.get("meta_linguistic_orchestration_layer") or []) == 3
    assert status.get("naming_protocol_aligned") is True
    assert status.get("linguistic_mutation_aligned") is True
    assert status.get("meta_linguistic_orchestration_aligned") is True
    assert status.get("meta_linguistic_governance_aligned") is True


def test_alt18_project_infi_law_planes_at_v113():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert len(status.get("law_cycle_posture") or []) == 3
    assert len(status.get("turn_admission_posture") or []) == 3
    assert len(status.get("governance_control_posture") or []) == 3
    assert status.get("project_infi_law_aligned") is True


def test_alt17_authority_protocol_integrity_planes_at_v112():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert len(status.get("protocol_posture") or []) == 3
    assert len(status.get("authority_shell_posture") or []) == 3
    assert len(status.get("response_integrity_posture") or []) == 3
    assert status.get("protocol_aligned") is True
    assert status.get("authority_shell_aligned") is True
    assert status.get("response_integrity_aligned") is True
    assert status.get("authority_protocol_integrity_aligned") is True


def test_alt15_lobe_voice_planes_at_v111():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert len(status.get("executive_attention_posture") or []) == 3
    assert len(status.get("deliberation_planning_posture") or []) == 3
    assert len(status.get("voice_execution_posture") or []) == 3
    assert status.get("executive_attention_aligned") is True
    assert status.get("deliberation_planning_aligned") is True
    assert status.get("voice_execution_aligned") is True
    assert status.get("nova_lobe_voice_aligned") is True


def test_alt12_planes_aligned_at_v112_alongside_alt13_and_alt14():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    assert status.get("operator_cognition_coherence_fabric_version") == (
        "operator_cognition_coherence_fabric.v1.17"
    )
    assert len(status.get("otem_lane_posture") or []) == 3
    assert len(status.get("predictive_lane_posture") or []) == 3
    assert len(status.get("execution_depth_posture") or []) == 3
    assert status.get("otem_lane_aligned") is True
    assert status.get("predictive_lane_aligned") is True
    assert status.get("execution_depth_aligned") is True
    assert len(status.get("constitutional_creative_posture") or []) == 5
    assert len(status.get("story_chain_posture") or []) == 3
    assert len(status.get("module_governance_posture") or []) == 1
    assert status.get("constitutional_creative_aligned") is True
    assert status.get("story_chain_aligned") is True
    assert status.get("module_governance_aligned") is True
    assert len(status.get("perception_posture") or []) == 3
    assert len(status.get("spatial_symbolic_posture") or []) == 3
    assert len(status.get("route_choice_posture") or []) == 3
    assert status.get("perception_aligned") is True
    assert status.get("spatial_symbolic_aligned") is True
    assert status.get("route_choice_aligned") is True


def test_perception_posture_includes_alt14_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("perception_posture") or []}
    assert organs == {
        "document_vision_organ",
        "ui_vision_organ",
        "perception_gateway_organ",
    }
    assert status.get("perception_aligned") is True


def test_spatial_symbolic_posture_includes_alt14_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("spatial_symbolic_posture") or []}
    assert organs == {
        "spatial_reasoning_organ",
        "mystic_engine_organ",
        "perception_lane_organ",
    }
    assert status.get("spatial_symbolic_aligned") is True


def test_route_choice_posture_includes_alt14_organs():
    status = build_coherence_fabric_status(root=Path(__file__).resolve().parents[1])
    organs = {item["organ_id"] for item in status.get("route_choice_posture") or []}
    assert organs == {
        "route_choice_organ",
        "specialist_route_organ",
        "provider_route_organ",
    }
    assert status.get("route_choice_aligned") is True
