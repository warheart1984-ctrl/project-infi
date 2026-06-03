"""Promotion Engine — full-auto SSP lifecycle stage transitions."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._audit import append_audit
from src.governance_organs._paths import repo_root, runtime_governance_dir
from src.governance_organs.genome_engine import GenomeEngine, load_json

STAGE_ORDER = ("concept", "prototype", "mvp", "governed")

GENE_GATES: dict[str, str] = {
    "recipe_module": "recipe-module-gate",
    "imagine_generator": "imagine-generator-gate",
    "human_voice_extraction": "human-voice-extraction-gate",
    "narrative_trust_pack": "narrative-gate",
    "forensic_triangulation": "triangulation-gate",
    "cisiv_operator_lineage_console": "lineage-gate",
    "safety_envelope_organ": "safety-envelope-gate",
    "operator_profile_organ": "operator-profile-gate",
    "reflection_runtime_organ": "reflection-runtime-gate",
    "memory_runtime_organ": "memory-runtime-gate",
    "capability_service_bridge": "capability-bridge-gate",
    "jarvis_memory_board": "memory-board-gate",
    "governed_direct_pipeline": "governed-pipeline-gate",
    "adaptive_lane_organ": "adaptive-lane-gate",
    "operator_cognition_coherence_fabric": "coherence-fabric-gate",
    "continuity_witness_organ": "continuity-witness-gate",
    "narrative_continuity_organ": "narrative-continuity-gate",
    "intent_agency_organ": "intent-agency-gate",
    "phase_gate_organ": "phase-gate-organ-gate",
    "realtime_event_cause_predictor_organ": "realtime-predictor-organ-gate",
    "invariant_engine_organ": "invariant-engine-organ-gate",
    "verification_gate_organ": "verification-gate-organ-gate",
    "memory_path_governance_organ": "memory-path-governance-organ-gate",
    "knowledge_authority_organ": "knowledge-authority-organ-gate",
    "scorpion_bridge_organ": "scorpion-bridge-organ-gate",
    "mechanic_handoff_organ": "mechanic-handoff-organ-gate",
    "forensic_triangulation_organ": "forensic-triangulation-organ-gate",
    "immune_observe_organ": "immune-observe-organ-gate",
    "policy_gate_organ": "policy-gate-organ-gate",
    "predictor_immune_bridge_organ": "predictor-immune-bridge-organ-gate",
    "cognitive_bridge_organ": "cognitive-bridge-organ-gate",
    "governed_event_chain_organ": "governed-event-chain-organ-gate",
    "tracing_spine_organ": "tracing-spine-organ-gate",
    "mission_board_organ": "mission-board-organ-gate",
    "aris_boundary_organ": "aris-boundary-organ-gate",
    "capability_module_organ": "capability-module-organ-gate",
    "patchforge_organ": "patchforge-organ-gate",
    "change_scope_organ": "change-scope-organ-gate",
    "patch_verification_organ": "patch-verification-organ-gate",
    "otem_bounded_organ": "otem-bounded-organ-gate",
    "direct_challenge_organ": "direct-challenge-organ-gate",
    "orchestration_spine_organ": "orchestration-spine-organ-gate",
    "operator_health_sentinel_organ": "operator-health-sentinel-organ-gate",
    "governed_realtime_lane_organ": "governed-realtime-lane-organ-gate",
    "v8_runtime_organ": "v8-runtime-organ-gate",
    "patch_apply_organ": "patch-apply-organ-gate",
    "patch_execution_preview_organ": "patch-execution-preview-organ-gate",
    "run_ledger_organ": "run-ledger-organ-gate",
    "ul_lineage_console_organ": "ul-lineage-console-organ-gate",
    "module_governance_organ": "module-governance-organ-gate",
    "recipe_module_organ": "recipe-module-organ-gate",
    "imagine_generator_organ": "imagine-generator-organ-gate",
    "story_forge_lane_organ": "story-forge-lane-organ-gate",
    "beatbox_lane_organ": "beatbox-lane-organ-gate",
    "speakers_lane_organ": "speakers-lane-organ-gate",
    "human_voice_extraction_organ": "human-voice-extraction-organ-gate",
    "narrative_trust_pack_organ": "narrative-trust-pack-organ-gate",
    "story_forge_launcher_organ": "story-forge-launcher-organ-gate",
    "movie_renderer_lane_organ": "movie-renderer-lane-organ-gate",
    "text_game_to_video_organ": "text-game-to-video-organ-gate",
    "game_front_door_organ": "game-front-door-organ-gate",
    "text_to_3d_world_lane_organ": "text-to-3d-world-lane-organ-gate",
    "world_pack_lane_organ": "world-pack-lane-organ-gate",
    "document_vision_organ": "document-vision-organ-gate",
    "ui_vision_organ": "ui-vision-organ-gate",
    "perception_gateway_organ": "perception-gateway-organ-gate",
    "spatial_reasoning_organ": "spatial-reasoning-organ-gate",
    "mystic_engine_organ": "mystic-engine-organ-gate",
    "perception_lane_organ": "perception-lane-organ-gate",
    "route_choice_organ": "route-choice-organ-gate",
    "specialist_route_organ": "specialist-route-organ-gate",
    "provider_route_organ": "provider-route-organ-gate",
    "reasoning_executive_organ": "reasoning-executive-organ-gate",
    "attention_organ": "attention-organ-gate",
    "coherence_projection_organ": "coherence-projection-organ-gate",
    "deliberation_organ": "deliberation-organ-gate",
    "planning_organ": "planning-organ-gate",
    "cortex_arcs_organ": "cortex-arcs-organ-gate",
    "cognitive_execution_organ": "cognitive-execution-organ-gate",
    "speaking_runtime_organ": "speaking-runtime-organ-gate",
    "nova_face_organ": "nova-face-organ-gate",
    "ai_factory_organ": "ai-factory-organ-gate",
    "cogos_runtime_bridge_organ": "cogos-runtime-bridge-organ-gate",
    "wolf_rehydration_organ": "wolf-rehydration-organ-gate",
    "forge_contractor_organ": "forge-contractor-organ-gate",
    "forge_eval_organ": "forge-eval-organ-gate",
    "evolve_engine_organ": "evolve-engine-organ-gate",
    "slingshot_organ": "slingshot-organ-gate",
    "operator_workbench_organ": "operator-workbench-organ-gate",
    "workflow_shell_organ": "workflow-shell-organ-gate",
    "jarvis_protocol_organ": "jarvis-protocol-organ-gate",
    "reasoning_contract_organ": "reasoning-contract-organ-gate",
    "jarvis_reasoning_lane_organ": "jarvis-reasoning-lane-organ-gate",
    "conversation_memory_organ": "conversation-memory-organ-gate",
    "continuity_substrate_organ": "continuity-substrate-organ-gate",
    "jarvis_operator_organ": "jarvis-operator-organ-gate",
    "anti_drift_organ": "anti-drift-organ-gate",
    "prompt_assembly_organ": "prompt-assembly-organ-gate",
    "output_integrity_organ": "output-integrity-organ-gate",
    "project_infi_state_machine_organ": "project-infi-state-machine-organ-gate",
    "project_infi_law_organ": "project-infi-law-organ-gate",
    "run_ledger_binding_organ": "run-ledger-binding-organ-gate",
    "chat_turn_governance_organ": "chat-turn-governance-organ-gate",
    "aais_ul_substrate_organ": "aais-ul-substrate-organ-gate",
    "aris_integration_organ": "aris-integration-organ-gate",
    "governance_layer_organ": "governance-layer-organ-gate",
    "security_protocol_organ": "security-protocol-organ-gate",
    "system_guard_organ": "system-guard-organ-gate",
    "launcher_organ": "launcher-organ-gate",
    "aais_doctor_organ": "aais-doctor-organ-gate",
    "workflow_runtime_organ": "workflow-runtime-organ-gate",
    "jarvis_console_surface_organ": "jarvis-console-surface-organ-gate",
    "memory_bank_surface_organ": "memory-bank-surface-organ-gate",
    "dashboard_surface_organ": "dashboard-surface-organ-gate",
    "nova_landing_surface_organ": "nova-landing-surface-organ-gate",
    "aais_composed_runtime_organ": "aais-composed-runtime-organ-gate",
    "api_gateway_organ": "api-gateway-organ-gate",
    "memory_smith_organ": "memory-smith-organ-gate",
    "operator_workspace_organ": "operator-workspace-organ-gate",
    "jarvis_runs_organ": "jarvis-runs-organ-gate",
    "state_hygiene_organ": "state-hygiene-organ-gate",
    "blueprint_posture_organ": "blueprint-posture-organ-gate",
    "workflow_interfaces_organ": "workflow-interfaces-organ-gate",
    "platform_console_interfaces_organ": "platform-console-interfaces-organ-gate",
    "operator_console_interface_organ": "operator-console-interface-organ-gate",
    "nova_workspace_interface_organ": "nova-workspace-interface-organ-gate",
    "creative_core_runtime_organ": "creative-core-runtime-organ-gate",
    "v9_core_organ": "v9-core-organ-gate",
    "v9_runtime_organ": "v9-runtime-organ-gate",
    "v10_core_organ": "v10-core-organ-gate",
    "v10_runtime_organ": "v10-runtime-organ-gate",
    "v10_action_engine_organ": "v10-action-engine-organ-gate",
    "creative_capability_bridge_organ": "creative-capability-bridge-organ-gate",
    "creative_operator_handoff_organ": "creative-operator-handoff-organ-gate",
    "creative_console_interface_organ": "creative-console-interface-organ-gate",
    "naming_protocol_organ": "naming-protocol-organ-gate",
    "naming_genome_organ": "naming-genome-organ-gate",
    "linguistic_mutation_organ": "linguistic-mutation-organ-gate",
    "mythic_engineering_translator_organ": "mythic-engineering-translator-organ-gate",
    "linguistic_drift_predictor_organ": "linguistic-drift-predictor-organ-gate",
    "linguistic_lineage_viz_organ": "linguistic-lineage-viz-organ-gate",
    "linguistic_remediation_organ": "linguistic-remediation-organ-gate",
    "linguistic_cascade_organ": "linguistic-cascade-organ-gate",
    "meta_linguistic_governance_organ": "meta-linguistic-governance-organ-gate",
    "linguistic_drift_forecast_organ": "linguistic-drift-forecast-organ-gate",
    "linguistic_preemptive_remediation_organ": "linguistic-preemptive-remediation-organ-gate",
    "linguistic_predictive_governance_organ": "linguistic-predictive-governance-organ-gate",
    "linguistic_predictive_cycle_history_organ": "linguistic-predictive-cycle-history-organ-gate",
    "linguistic_governance_cycle_organ": "linguistic-governance-cycle-organ-gate",
    "linguistic_governance_cycle_history_organ": "linguistic-governance-cycle-history-organ-gate",
    "linguistic_forecast_consumption_organ": "linguistic-forecast-consumption-organ-gate",
    "linguistic_cycle_optimization_organ": "linguistic-cycle-optimization-organ-gate",
    "linguistic_closed_loop_fabric_organ": "linguistic-closed-loop-fabric-organ-gate",
    "linguistic_forecast_calibration_organ": "linguistic-forecast-calibration-organ-gate",
    "linguistic_governance_queue_organ": "linguistic-governance-queue-organ-gate",
    "linguistic_full_governance_cycle_organ": "linguistic-full-governance-cycle-organ-gate",
    "linguistic_governance_attestation_organ": "linguistic-governance-attestation-organ-gate",
    "linguistic_forecast_archive_organ": "linguistic-forecast-archive-organ-gate",
    "linguistic_drift_report_organ": "linguistic-drift-report-organ-gate",
    "linguistic_governance_work_order_organ": "linguistic-governance-work-order-organ-gate",
    "linguistic_governance_cadence_organ": "linguistic-governance-cadence-organ-gate",
    "linguistic_forecast_calibration_report_organ": "linguistic-forecast-calibration-report-organ-gate",
    "linguistic_full_governance_cycle_history_organ": "linguistic-full-governance-cycle-history-organ-gate",
    "meta_linguistic_registry_organ": "meta-linguistic-registry-organ-gate",
    "linguistic_subsystem_promotion_organ": "linguistic-subsystem-promotion-organ-gate",
    "linguistic_governed_lifecycle_fabric_organ": "linguistic-governed-lifecycle-fabric-organ-gate",
    "linguistic_governance_day_organ": "linguistic-governance-day-organ-gate",
    "linguistic_work_order_history_organ": "linguistic-work-order-history-organ-gate",
    "linguistic_attestation_history_organ": "linguistic-attestation-history-organ-gate",
}

GATE_SCRIPTS: dict[str, list[str]] = {
    "recipe-module-gate": [".github/scripts/check-recipe-module-governance.py"],
    "imagine-generator-gate": [".github/scripts/check-imagine-generator-governance.py"],
    "human-voice-extraction-gate": [
        ".github/scripts/check-human-voice-extraction-governance.py"
    ],
    "narrative-gate": [".github/scripts/check-narrative-governance.py"],
    "triangulation-gate": [".github/scripts/check-triangulation-governance.py"],
    "lineage-gate": [".github/scripts/check-lineage-governance.py"],
    "ssp-gate": ["tools/governance/check_ssp_completeness.py"],
    "genome-gate": ["tools/governance/check_subsystem_genome.py"],
    "safety-envelope-gate": [".github/scripts/check-safety-envelope-governance.py"],
    "operator-profile-gate": [".github/scripts/check-operator-profile-governance.py"],
    "reflection-runtime-gate": [".github/scripts/check-reflection-runtime-governance.py"],
    "memory-runtime-gate": [".github/scripts/check-memory-runtime-governance.py"],
    "adaptive-lane-gate": [".github/scripts/check-adaptive-lane-governance.py"],
    "coherence-fabric-gate": [".github/scripts/check-coherence-fabric-governance.py"],
    "capability-bridge-gate": [".github/scripts/check-capability-bridge-governance.py"],
    "memory-board-gate": [".github/scripts/check-memory-board-governance.py"],
    "governed-pipeline-gate": [".github/scripts/check-governed-pipeline-governance.py"],
    "continuity-witness-gate": [".github/scripts/check-continuity-witness-governance.py"],
    "narrative-continuity-gate": [".github/scripts/check-narrative-continuity-governance.py"],
    "intent-agency-gate": [".github/scripts/check-intent-agency-governance.py"],
    "phase-gate-organ-gate": [".github/scripts/check-phase-gate-organ-governance.py"],
    "realtime-predictor-organ-gate": [
        ".github/scripts/check-realtime-predictor-organ-governance.py"
    ],
    "invariant-engine-organ-gate": [
        ".github/scripts/check-invariant-engine-organ-governance.py"
    ],
    "verification-gate-organ-gate": [
        ".github/scripts/check-verification-gate-organ-governance.py"
    ],
    "memory-path-governance-organ-gate": [
        ".github/scripts/check-memory-path-governance-organ-governance.py"
    ],
    "knowledge-authority-organ-gate": [
        ".github/scripts/check-knowledge-authority-organ-governance.py"
    ],
    "scorpion-bridge-organ-gate": [
        ".github/scripts/check-scorpion-bridge-organ-governance.py"
    ],
    "mechanic-handoff-organ-gate": [
        ".github/scripts/check-mechanic-handoff-organ-governance.py"
    ],
    "forensic-triangulation-organ-gate": [
        ".github/scripts/check-forensic-triangulation-organ-governance.py"
    ],
    "immune-observe-organ-gate": [
        ".github/scripts/check-immune-observe-organ-governance.py"
    ],
    "policy-gate-organ-gate": [".github/scripts/check-policy-gate-organ-governance.py"],
    "predictor-immune-bridge-organ-gate": [
        ".github/scripts/check-predictor-immune-bridge-organ-governance.py"
    ],
    "cognitive-bridge-organ-gate": [
        ".github/scripts/check-cognitive-bridge-organ-governance.py"
    ],
    "governed-event-chain-organ-gate": [
        ".github/scripts/check-governed-event-chain-organ-governance.py"
    ],
    "tracing-spine-organ-gate": [".github/scripts/check-tracing-spine-organ-governance.py"],
    "mission-board-organ-gate": [".github/scripts/check-mission-board-organ-governance.py"],
    "aris-boundary-organ-gate": [".github/scripts/check-aris-boundary-organ-governance.py"],
    "capability-module-organ-gate": [
        ".github/scripts/check-capability-module-organ-governance.py"
    ],
    "patchforge-organ-gate": [".github/scripts/check-patchforge-organ-governance.py"],
    "change-scope-organ-gate": [".github/scripts/check-change-scope-organ-governance.py"],
    "patch-verification-organ-gate": [
        ".github/scripts/check-patch-verification-organ-governance.py"
    ],
    "otem-bounded-organ-gate": [".github/scripts/check-otem-bounded-organ-governance.py"],
    "direct-challenge-organ-gate": [
        ".github/scripts/check-direct-challenge-organ-governance.py"
    ],
    "orchestration-spine-organ-gate": [
        ".github/scripts/check-orchestration-spine-organ-governance.py"
    ],
    "operator-health-sentinel-organ-gate": [
        ".github/scripts/check-operator-health-sentinel-organ-governance.py"
    ],
    "governed-realtime-lane-organ-gate": [
        ".github/scripts/check-governed-realtime-lane-organ-governance.py"
    ],
    "v8-runtime-organ-gate": [".github/scripts/check-v8-runtime-organ-governance.py"],
    "patch-apply-organ-gate": [".github/scripts/check-patch-apply-organ-governance.py"],
    "patch-execution-preview-organ-gate": [
        ".github/scripts/check-patch-execution-preview-organ-governance.py"
    ],
    "run-ledger-organ-gate": [".github/scripts/check-run-ledger-organ-governance.py"],
    "ul-lineage-console-organ-gate": [
        ".github/scripts/check-ul-lineage-console-organ-governance.py"
    ],
    "module-governance-organ-gate": [
        ".github/scripts/check-module-governance-organ-governance.py"
    ],
    "recipe-module-organ-gate": [".github/scripts/check-recipe-module-organ-governance.py"],
    "imagine-generator-organ-gate": [
        ".github/scripts/check-imagine-generator-organ-governance.py"
    ],
    "story-forge-lane-organ-gate": [
        ".github/scripts/check-story-forge-lane-organ-governance.py"
    ],
    "beatbox-lane-organ-gate": [".github/scripts/check-beatbox-lane-organ-governance.py"],
    "speakers-lane-organ-gate": [".github/scripts/check-speakers-lane-organ-governance.py"],
    "human-voice-extraction-organ-gate": [
        ".github/scripts/check-human-voice-extraction-organ-governance.py"
    ],
    "narrative-trust-pack-organ-gate": [
        ".github/scripts/check-narrative-trust-pack-organ-governance.py"
    ],
    "story-forge-launcher-organ-gate": [
        ".github/scripts/check-story-forge-launcher-organ-governance.py"
    ],
    "movie-renderer-lane-organ-gate": [
        ".github/scripts/check-movie-renderer-lane-organ-governance.py"
    ],
    "text-game-to-video-organ-gate": [
        ".github/scripts/check-text-game-to-video-organ-governance.py"
    ],
    "game-front-door-organ-gate": [
        ".github/scripts/check-game-front-door-organ-governance.py"
    ],
    "text-to-3d-world-lane-organ-gate": [
        ".github/scripts/check-text-to-3d-world-lane-organ-governance.py"
    ],
    "world-pack-lane-organ-gate": [
        ".github/scripts/check-world-pack-lane-organ-governance.py"
    ],
    "document-vision-organ-gate": [
        ".github/scripts/check-document-vision-organ-governance.py"
    ],
    "ui-vision-organ-gate": [".github/scripts/check-ui-vision-organ-governance.py"],
    "perception-gateway-organ-gate": [
        ".github/scripts/check-perception-gateway-organ-governance.py"
    ],
    "spatial-reasoning-organ-gate": [
        ".github/scripts/check-spatial-reasoning-organ-governance.py"
    ],
    "mystic-engine-organ-gate": [".github/scripts/check-mystic-engine-organ-governance.py"],
    "perception-lane-organ-gate": [
        ".github/scripts/check-perception-lane-organ-governance.py"
    ],
    "route-choice-organ-gate": [".github/scripts/check-route-choice-organ-governance.py"],
    "specialist-route-organ-gate": [
        ".github/scripts/check-specialist-route-organ-governance.py"
    ],
    "provider-route-organ-gate": [".github/scripts/check-provider-route-organ-governance.py"],
    "reasoning-executive-organ-gate": [
        ".github/scripts/check-reasoning-executive-organ-governance.py"
    ],
    "attention-organ-gate": [".github/scripts/check-attention-organ-governance.py"],
    "coherence-projection-organ-gate": [
        ".github/scripts/check-coherence-projection-organ-governance.py"
    ],
    "deliberation-organ-gate": [".github/scripts/check-deliberation-organ-governance.py"],
    "planning-organ-gate": [".github/scripts/check-planning-organ-governance.py"],
    "cortex-arcs-organ-gate": [".github/scripts/check-cortex-arcs-organ-governance.py"],
    "cognitive-execution-organ-gate": [
        ".github/scripts/check-cognitive-execution-organ-governance.py"
    ],
    "speaking-runtime-organ-gate": [
        ".github/scripts/check-speaking-runtime-organ-governance.py"
    ],
    "nova-face-organ-gate": [".github/scripts/check-nova-face-organ-governance.py"],
    "ai-factory-organ-gate": [".github/scripts/check-ai-factory-organ-governance.py"],
    "cogos-runtime-bridge-organ-gate": [
        ".github/scripts/check-cogos-runtime-bridge-organ-governance.py"
    ],
    "wolf-rehydration-organ-gate": [
        ".github/scripts/check-wolf-rehydration-organ-governance.py"
    ],
    "forge-contractor-organ-gate": [
        ".github/scripts/check-forge-contractor-organ-governance.py"
    ],
    "forge-eval-organ-gate": [".github/scripts/check-forge-eval-organ-governance.py"],
    "evolve-engine-organ-gate": [".github/scripts/check-evolve-engine-organ-governance.py"],
    "slingshot-organ-gate": [".github/scripts/check-slingshot-organ-governance.py"],
    "operator-workbench-organ-gate": [
        ".github/scripts/check-operator-workbench-organ-governance.py"
    ],
    "workflow-shell-organ-gate": [".github/scripts/check-workflow-shell-organ-governance.py"],
    "jarvis-protocol-organ-gate": [
        ".github/scripts/check-jarvis-protocol-organ-governance.py"
    ],
    "reasoning-contract-organ-gate": [
        ".github/scripts/check-reasoning-contract-organ-governance.py"
    ],
    "jarvis-reasoning-lane-organ-gate": [
        ".github/scripts/check-jarvis-reasoning-lane-organ-governance.py"
    ],
    "conversation-memory-organ-gate": [
        ".github/scripts/check-conversation-memory-organ-governance.py"
    ],
    "continuity-substrate-organ-gate": [
        ".github/scripts/check-continuity-substrate-organ-governance.py"
    ],
    "jarvis-operator-organ-gate": [
        ".github/scripts/check-jarvis-operator-organ-governance.py"
    ],
    "anti-drift-organ-gate": [".github/scripts/check-anti-drift-organ-governance.py"],
    "prompt-assembly-organ-gate": [
        ".github/scripts/check-prompt-assembly-organ-governance.py"
    ],
    "output-integrity-organ-gate": [
        ".github/scripts/check-output-integrity-organ-governance.py"
    ],
    "project-infi-state-machine-organ-gate": [
        ".github/scripts/check-project-infi-state-machine-organ-governance.py"
    ],
    "project-infi-law-organ-gate": [
        ".github/scripts/check-project-infi-law-organ-governance.py"
    ],
    "run-ledger-binding-organ-gate": [
        ".github/scripts/check-run-ledger-binding-organ-governance.py"
    ],
    "chat-turn-governance-organ-gate": [
        ".github/scripts/check-chat-turn-governance-organ-governance.py"
    ],
    "aais-ul-substrate-organ-gate": [
        ".github/scripts/check-aais-ul-substrate-organ-governance.py"
    ],
    "aris-integration-organ-gate": [
        ".github/scripts/check-aris-integration-organ-governance.py"
    ],
    "governance-layer-organ-gate": [
        ".github/scripts/check-governance-layer-organ-governance.py"
    ],
    "security-protocol-organ-gate": [
        ".github/scripts/check-security-protocol-organ-governance.py"
    ],
    "system-guard-organ-gate": [
        ".github/scripts/check-system-guard-organ-governance.py"
    ],
    "launcher-organ-gate": [".github/scripts/check-launcher-organ-governance.py"],
    "aais-doctor-organ-gate": [".github/scripts/check-aais-doctor-organ-governance.py"],
    "workflow-runtime-organ-gate": [
        ".github/scripts/check-workflow-runtime-organ-governance.py"
    ],
    "jarvis-console-surface-organ-gate": [
        ".github/scripts/check-jarvis-console-surface-organ-governance.py"
    ],
    "memory-bank-surface-organ-gate": [
        ".github/scripts/check-memory-bank-surface-organ-governance.py"
    ],
    "dashboard-surface-organ-gate": [
        ".github/scripts/check-dashboard-surface-organ-governance.py"
    ],
    "nova-landing-surface-organ-gate": [
        ".github/scripts/check-nova-landing-surface-organ-governance.py"
    ],
    "aais-composed-runtime-organ-gate": [
        ".github/scripts/check-aais-composed-runtime-organ-governance.py"
    ],
    "api-gateway-organ-gate": [".github/scripts/check-api-gateway-organ-governance.py"],
    "memory-smith-organ-gate": [
        ".github/scripts/check-memory-smith-organ-governance.py"
    ],
    "operator-workspace-organ-gate": [
        ".github/scripts/check-operator-workspace-organ-governance.py"
    ],
    "jarvis-runs-organ-gate": [".github/scripts/check-jarvis-runs-organ-governance.py"],
    "state-hygiene-organ-gate": [
        ".github/scripts/check-state-hygiene-organ-governance.py"
    ],
    "blueprint-posture-organ-gate": [
        ".github/scripts/check-blueprint-posture-organ-governance.py"
    ],
    "workflow-interfaces-organ-gate": [
        ".github/scripts/check-workflow-interfaces-organ-governance.py"
    ],
    "platform-console-interfaces-organ-gate": [
        ".github/scripts/check-platform-console-interfaces-organ-governance.py"
    ],
    "operator-console-interface-organ-gate": [
        ".github/scripts/check-operator-console-interface-organ-governance.py"
    ],
    "nova-workspace-interface-organ-gate": [
        ".github/scripts/check-nova-workspace-interface-organ-governance.py"
    ],
    "creative-core-runtime-organ-gate": [
        ".github/scripts/check-creative-core-runtime-organ-governance.py"
    ],
    "v9-core-organ-gate": [".github/scripts/check-v9-core-organ-governance.py"],
    "v9-runtime-organ-gate": [".github/scripts/check-v9-runtime-organ-governance.py"],
    "v10-core-organ-gate": [".github/scripts/check-v10-core-organ-governance.py"],
    "v10-runtime-organ-gate": [
        ".github/scripts/check-v10-runtime-organ-governance.py"
    ],
    "v10-action-engine-organ-gate": [
        ".github/scripts/check-v10-action-engine-organ-governance.py"
    ],
    "creative-capability-bridge-organ-gate": [
        ".github/scripts/check-creative-capability-bridge-organ-governance.py"
    ],
    "creative-operator-handoff-organ-gate": [
        ".github/scripts/check-creative-operator-handoff-organ-governance.py"
    ],
    "creative-console-interface-organ-gate": [
        ".github/scripts/check-creative-console-interface-organ-governance.py"
    ],
    "naming-protocol-organ-gate": [
        ".github/scripts/check-naming-protocol-organ-governance.py"
    ],
    "naming-genome-organ-gate": [
        ".github/scripts/check-naming-genome-organ-governance.py"
    ],
    "linguistic-mutation-organ-gate": [
        ".github/scripts/check-linguistic-mutation-organ-governance.py"
    ],
    "mythic-engineering-translator-organ-gate": [
        ".github/scripts/check-mythic-engineering-translator-organ-governance.py"
    ],
    "linguistic-drift-predictor-organ-gate": [
        ".github/scripts/check-linguistic-drift-predictor-organ-governance.py"
    ],
    "linguistic-lineage-viz-organ-gate": [
        ".github/scripts/check-linguistic-lineage-viz-organ-governance.py"
    ],
    "linguistic-remediation-organ-gate": [
        ".github/scripts/check-linguistic-remediation-organ-governance.py"
    ],
    "linguistic-cascade-organ-gate": [
        ".github/scripts/check-linguistic-cascade-organ-governance.py"
    ],
    "meta-linguistic-governance-organ-gate": [
        ".github/scripts/check-meta-linguistic-governance-organ-governance.py"
    ],
    "linguistic-drift-forecast-organ-gate": [
        ".github/scripts/check-linguistic-drift-forecast-organ-governance.py"
    ],
    "linguistic-preemptive-remediation-organ-gate": [
        ".github/scripts/check-linguistic-preemptive-remediation-organ-governance.py"
    ],
    "linguistic-predictive-governance-organ-gate": [
        ".github/scripts/check-linguistic-predictive-governance-organ-governance.py"
    ],
    "linguistic-predictive-cycle-history-organ-gate": [
        ".github/scripts/check-linguistic-predictive-cycle-history-organ-governance.py"
    ],
    "linguistic-governance-cycle-organ-gate": [
        ".github/scripts/check-linguistic-governance-cycle-organ-governance.py"
    ],
    "linguistic-governance-cycle-history-organ-gate": [
        ".github/scripts/check-linguistic-governance-cycle-history-organ-governance.py"
    ],
    "linguistic-forecast-consumption-organ-gate": [
        ".github/scripts/check-linguistic-forecast-consumption-organ-governance.py"
    ],
    "linguistic-cycle-optimization-organ-gate": [
        ".github/scripts/check-linguistic-cycle-optimization-organ-governance.py"
    ],
    "linguistic-closed-loop-fabric-organ-gate": [
        ".github/scripts/check-linguistic-closed-loop-fabric-organ-governance.py"
    ],
    "linguistic-forecast-calibration-organ-gate": [
        ".github/scripts/check-linguistic-forecast-calibration-organ-governance.py"
    ],
    "linguistic-governance-queue-organ-gate": [
        ".github/scripts/check-linguistic-governance-queue-organ-governance.py"
    ],
    "linguistic-full-governance-cycle-organ-gate": [
        ".github/scripts/check-linguistic-full-governance-cycle-organ-governance.py"
    ],
    "linguistic-governance-attestation-organ-gate": [
        ".github/scripts/check-linguistic-governance-attestation-organ-governance.py"
    ],
    "linguistic-forecast-archive-organ-gate": [
        ".github/scripts/check-linguistic-forecast-archive-organ-governance.py"
    ],
    "linguistic-drift-report-organ-gate": [
        ".github/scripts/check-linguistic-drift-report-organ-governance.py"
    ],
    "linguistic-governance-work-order-organ-gate": [
        ".github/scripts/check-linguistic-governance-work-order-organ-governance.py"
    ],
    "linguistic-governance-cadence-organ-gate": [
        ".github/scripts/check-linguistic-governance-cadence-organ-governance.py"
    ],
    "linguistic-forecast-calibration-report-organ-gate": [
        ".github/scripts/check-linguistic-forecast-calibration-report-organ-governance.py"
    ],
    "linguistic-full-governance-cycle-history-organ-gate": [
        ".github/scripts/check-linguistic-full-governance-cycle-history-organ-governance.py"
    ],
    "meta-linguistic-registry-organ-gate": [
        ".github/scripts/check-meta-linguistic-registry-organ-governance.py"
    ],
    "linguistic-subsystem-promotion-organ-gate": [
        ".github/scripts/check-linguistic-subsystem-promotion-organ-governance.py"
    ],
    "linguistic-governed-lifecycle-fabric-organ-gate": [
        ".github/scripts/check-linguistic-governed-lifecycle-fabric-organ-governance.py"
    ],
    "linguistic-governance-day-organ-gate": [
        ".github/scripts/check-linguistic-governance-day-organ-governance.py"
    ],
    "linguistic-work-order-history-organ-gate": [
        ".github/scripts/check-linguistic-work-order-history-organ-governance.py"
    ],
    "linguistic-attestation-history-organ-gate": [
        ".github/scripts/check-linguistic-attestation-history-organ-governance.py"
    ],
}

PROTOTYPE_GATE_STUB_GENES = frozenset(GENE_GATES.keys()) | frozenset(
    {
        "capability_service_bridge",
        "jarvis_memory_board",
        "governed_direct_pipeline",
    }
)

MUTATION_CONTRACT = "docs/contracts/AAIS_SUBSYSTEM_MUTATION_PATH.md"
RETIREMENT_CONTRACT = "docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md"


@dataclass
class PromotionDecision:
    gene: str
    passed: bool
    current_stage: str
    target_stage: str | None
    failures: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)


class PromotionEngine:
    def __init__(self, root: Path | None = None):
        self.root = root or repo_root()

    def _genome_path(self, gene: str) -> Path:
        path = GenomeEngine.registry().paths.get(gene)
        if path is None:
            raise KeyError(f"unknown gene: {gene}")
        return path

    def _read_genome(self, gene: str) -> dict[str, Any]:
        return load_json(self._genome_path(gene))

    def _write_genome(self, gene: str, data: dict[str, Any]) -> None:
        path = self._genome_path(gene)
        backup_dir = runtime_governance_dir() / "promotion_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(path, backup_dir / f"{gene}_{stamp}.genome.v1.json")
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        GenomeEngine.reload(self.root)

    def _run_gate(self, target: str) -> tuple[bool, str]:
        import sys

        scripts = GATE_SCRIPTS.get(target)
        if scripts:
            outputs: list[str] = []
            for script in scripts:
                path = self.root / script
                try:
                    proc = subprocess.run(
                        [sys.executable, str(path)],
                        cwd=self.root,
                        capture_output=True,
                        text=True,
                        timeout=600,
                        check=False,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    return False, str(exc)
                outputs.append((proc.stdout or "") + (proc.stderr or ""))
                if proc.returncode != 0:
                    return False, "\n".join(outputs).strip()
            return True, "\n".join(outputs).strip()

        try:
            proc = subprocess.run(
                ["make", target],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except FileNotFoundError:
            return False, "make not found and no gate script mapping"
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, str(exc)
        output = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, output.strip()

    def _has_cross_reference(self, gene: str, data: dict[str, Any]) -> bool:
        lineage = data.get("lineage") or {}
        if lineage.get("children"):
            return True
        for other_gene, other in GenomeEngine.registry().genomes.items():
            if gene in (other.get("lineage") or {}).get("children", []):
                return True
        return False

    def _has_invariant_tests(self, gene: str) -> bool:
        tests_dir = self.root / "tests"
        patterns = [
            f"test_{gene}.py",
            f"test_{gene.replace('_', '')}.py",
        ]
        for pattern in patterns:
            if (tests_dir / pattern).is_file():
                return True
        partial = gene.split("_")[0]
        for path in tests_dir.glob(f"test_*{partial}*.py"):
            if gene.replace("_", "") in path.name.replace("_", "") or gene in path.name:
                return True
        return False

    def _contracts_cover_lifecycle(self, data: dict[str, Any]) -> bool:
        contracts = [str(c) for c in (data.get("governance") or {}).get("contracts") or []]
        has_mutation = any("MUTATION" in c.upper() for c in contracts)
        has_retirement = any("RETIREMENT" in c.upper() for c in contracts)
        return has_mutation and has_retirement

    def _next_stage(self, current: str) -> str | None:
        if current not in STAGE_ORDER:
            return None
        idx = STAGE_ORDER.index(current)
        if idx + 1 >= len(STAGE_ORDER):
            return None
        return STAGE_ORDER[idx + 1]

    def evaluate(self, gene: str, *, run_gates: bool = True) -> PromotionDecision:
        reg = GenomeEngine.reload(self.root)
        if gene not in reg.genomes:
            return PromotionDecision(
                gene=gene,
                passed=False,
                current_stage="",
                target_stage=None,
                failures=[f"gene not in registry: {gene}"],
            )

        data = reg.genomes[gene]
        current = (data.get("identity") or {}).get("stage", "")
        target = self._next_stage(current)
        failures: list[str] = []
        artifacts: list[str] = []

        if target is None:
            return PromotionDecision(
                gene=gene,
                passed=True,
                current_stage=current,
                target_stage=None,
                failures=[],
                artifacts=["already at terminal promotable stage"],
            )

        if target == "prototype":
            if run_gates:
                ssp_ok, ssp_out = self._run_gate("ssp-gate")
                artifacts.append("make ssp-gate")
                if not ssp_ok:
                    failures.append(f"ssp-gate failed: {ssp_out[-400:]}")
            proof = data.get("proof") or {}
            for bundle in proof.get("bundles") or []:
                if "PROTOTYPE" in bundle.upper():
                    artifacts.append(bundle)
            surface = (data.get("runtime") or {}).get("surface") or []
            if not surface:
                failures.append("prototype requires runtime.surface entries")
            for entry in surface:
                if isinstance(entry, dict) and entry.get("isolated") is not True:
                    failures.append("prototype surface entries must be isolated")

        if target == "mvp":
            gate = GENE_GATES.get(gene)
            if gate:
                artifacts.append(f"make {gate}")
                if run_gates:
                    ok, out = self._run_gate(gate)
                    if not ok:
                        failures.append(f"{gate} failed: {out[-400:]}")
            else:
                failures.append(f"no gene gate defined for {gene}")
            proof = data.get("proof") or {}
            bundles = proof.get("bundles") or []
            if not bundles:
                failures.append("mvp requires proof.bundles")
            for bundle in bundles:
                if not (self.root / bundle).is_file():
                    failures.append(f"missing proof bundle: {bundle}")
            surface = (data.get("runtime") or {}).get("surface") or []
            if not surface:
                failures.append("mvp requires runtime.surface")

        if target == "governed":
            gate = GENE_GATES.get(gene)
            if gate:
                artifacts.append(f"make {gate}")
                if run_gates:
                    ok, out = self._run_gate(gate)
                    if not ok:
                        failures.append(f"{gate} failed: {out[-400:]}")
            artifacts.append("make genome-gate")
            if run_gates:
                ok, out = self._run_gate("genome-gate")
                if not ok:
                    failures.append(f"genome-gate failed: {out[-400:]}")
            if not self._has_invariant_tests(gene):
                failures.append("governed requires invariant tests under tests/")
            if not self._has_cross_reference(gene, data):
                failures.append(
                    "governed requires lineage.children or reference from another genome"
                )
            if not self._contracts_cover_lifecycle(data):
                if (self.root / MUTATION_CONTRACT).is_file() and (
                    self.root / RETIREMENT_CONTRACT
                ).is_file():
                    artifacts.append("lifecycle contracts injectable on governed apply")
                else:
                    failures.append(
                        "governed requires mutation and retirement contract docs on disk"
                    )
            proof = data.get("proof") or {}
            for bundle in proof.get("bundles") or []:
                if not (self.root / bundle).is_file():
                    failures.append(f"missing proof bundle: {bundle}")

        return PromotionDecision(
            gene=gene,
            passed=not failures,
            current_stage=current,
            target_stage=target,
            failures=failures,
            artifacts=artifacts,
        )

    def _append_logbook(self, gene: str, target: str, display_name: str) -> None:
        logbook = self.root / "docs/audit/LOGBOOK.md"
        title_map = {
            "prototype": "Prototype Promotion",
            "mvp": "MVP Promotion",
            "governed": "Governed Promotion",
        }
        title = title_map.get(target, f"{target.title()} Promotion")
        entry = (
            f"\n### {display_name} — {title} (Alt-4 Runtime)\n\n"
            f"- CISIV stage: `verification`\n"
            f"- scope: Promotion Engine full-auto — `{gene}` "
            f"`{target}` via Alt-4 runtime organ\n"
            f"- outcome: genome `identity.stage` and `proof.posture` set to `{target}`\n"
            f"- verification note: `make genome-gate`; `make alt4-gate`\n"
        )
        text = logbook.read_text(encoding="utf-8")
        if f"### {display_name} — {title} (Alt-4 Runtime)" in text:
            return
        logbook.write_text(text.rstrip() + entry, encoding="utf-8")

    def _update_subsystem_spec_governed(self, gene: str, display_name: str) -> None:
        spec_path = self.root / "docs/runtime/AAIS_SUBSYSTEM_SPEC.md"
        text = spec_path.read_text(encoding="utf-8")
        if f"| {display_name} | governed |" in text:
            return
        pattern = re.compile(
            rf"\| {re.escape(display_name)} \| partial \|",
        )
        replacement = f"| {display_name} | governed |"
        if pattern.search(text):
            spec_path.write_text(pattern.sub(replacement, text), encoding="utf-8")

    def apply(self, decision: PromotionDecision, *, dry_run: bool = False) -> PromotionDecision:
        append_audit(
            "promotion_audit.jsonl",
            {
                "action": "promotion_apply",
                "dry_run": dry_run,
                "gene": decision.gene,
                "target_stage": decision.target_stage,
                "passed": decision.passed,
                "failures": decision.failures,
            },
        )
        if not decision.passed or not decision.target_stage:
            return decision
        if decision.current_stage == decision.target_stage:
            return decision

        data = self._read_genome(decision.gene)
        identity = data.setdefault("identity", {})
        proof = data.setdefault("proof", {})
        schema = data.setdefault("schema", {})
        gov = data.setdefault("governance", {})
        retirement = data.setdefault("retirement", {})

        target = decision.target_stage
        identity["stage"] = target
        proof["posture"] = target

        if target == "governed":
            schema["frozen"] = True
            contracts = list(gov.get("contracts") or [])
            for path in (MUTATION_CONTRACT, RETIREMENT_CONTRACT):
                if path not in contracts:
                    contracts.append(path)
            gov["contracts"] = contracts
            if not retirement.get("path"):
                retirement["path"] = RETIREMENT_CONTRACT
            version = str(identity.get("version") or "1.0.0-mvp")
            if "mvp" in version:
                identity["version"] = version.replace("-mvp", "-governed")
            display = identity.get("display_name") or decision.gene

        if dry_run:
            return decision

        try:
            self._write_genome(decision.gene, data)
            display = (data.get("identity") or {}).get("display_name") or decision.gene
            self._append_logbook(decision.gene, target, display)
            if target == "governed":
                self._update_subsystem_spec_governed(decision.gene, display)
            ok, out = self._run_gate("genome-gate")
            if not ok:
                self.rollback(decision.gene)
                decision.passed = False
                decision.failures.append(f"post-apply genome-gate failed: {out[-400:]}")
        except Exception as exc:
            decision.passed = False
            decision.failures.append(f"apply failed: {exc}")
        return decision

    def rollback(self, gene: str) -> bool:
        backup_dir = runtime_governance_dir() / "promotion_backups"
        backups = sorted(backup_dir.glob(f"{gene}_*.genome.v1.json"))
        if not backups:
            return False
        latest = backups[-1]
        shutil.copy2(latest, self._genome_path(gene))
        GenomeEngine.reload(self.root)
        append_audit(
            "promotion_audit.jsonl",
            {"action": "promotion_rollback", "gene": gene, "restored": str(latest)},
        )
        return True

    def scan_all(
        self,
        *,
        apply: bool = False,
        dry_run: bool = False,
        run_gates: bool = True,
    ) -> list[PromotionDecision]:
        results: list[PromotionDecision] = []
        for gene in sorted(GenomeEngine.registry().genomes):
            decision = self.evaluate(gene, run_gates=run_gates)
            if apply and decision.passed and decision.target_stage:
                decision = self.apply(decision, dry_run=dry_run)
            results.append(decision)
        return results


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Alt-4 Promotion Engine")
    parser.add_argument("--gene", help="Subsystem gene to evaluate")
    parser.add_argument("--apply", action="store_true", help="Apply promotion if eligible")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate apply without writes")
    parser.add_argument("--scan-all", action="store_true", help="Scan entire registry")
    args = parser.parse_args()

    engine = PromotionEngine()
    GenomeEngine.validate_registry()

    if args.scan_all:
        results = engine.scan_all(apply=args.apply, dry_run=args.dry_run)
        failed = [r for r in results if not r.passed and r.target_stage]
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            print(
                f"[promotion] {status} {result.gene}: "
                f"{result.current_stage} -> {result.target_stage or '—'}"
            )
            for failure in result.failures:
                print(f"  - {failure}")
        return 1 if failed else 0

    if not args.gene:
        parser.error("--gene or --scan-all required")
        return 2

    decision = engine.evaluate(args.gene)
    if args.apply:
        decision = engine.apply(decision, dry_run=args.dry_run)
    print(json.dumps(decision.__dict__, indent=2))
    return 0 if decision.passed else 1


if __name__ == "__main__":
    import sys
    from pathlib import Path

    _root = Path(__file__).resolve().parents[2]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    raise SystemExit(main())
