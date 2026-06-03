"""Operator Cognition Coherence Fabric — read-only cross-plane snapshot."""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COHERENCE_FABRIC_SCHEMA_VERSION = "operator_cognition_coherence_fabric.v1.18"
GOVERNANCE_PROJECTION_DOC = "docs/subsystems/platform/OPERATOR_COGNITION_COHERENCE_FABRIC.md"
MAX_ENVELOPE_MODES = 6
MAX_FIELD_LEN = 120

from src.adaptive_lane_organ import LaneResolution, load_awakened_lanes, resolve_lane_for_gene
from src.capability_service_bridge import to_bridge_envelope
from src.governed_direct_pipeline import (
    DIRECT_COGNITIVE_LANE,
    PIPELINE_ID,
    PIPELINE_VERSION,
    to_pipeline_envelope,
)
from src.governance_organs._paths import repo_root
from src.jarvis_memory_board import (
    build_default_memory_controller,
    build_memory_board_snapshot,
    to_memory_board_envelope,
)
from src.operator_profile_organ import build_operator_profile
from src.safety_envelope import build_envelope_status


@dataclass
class CoherenceExecuteResult:
    allowed: bool
    reason: str | None = None


def _normalize_cap(capability_id: str | None) -> str:
    return str(capability_id or "").replace("-", "_").strip().lower()


def _is_policy_capability(
    capability_id: str | None,
    lane_resolution: LaneResolution,
) -> bool:
    cap = _normalize_cap(capability_id)
    if not cap or not lane_resolution.capabilities:
        return False
    policy_caps = {_normalize_cap(item) for item in lane_resolution.capabilities}
    return cap in policy_caps


def evaluate_bridge_coherence(
    *,
    capability_id: str | None,
    lane_resolution: LaneResolution,
    bridge_governance_mode: str,
    fabric_genes_aligned: bool,
    safety_halt: bool,
    authority_lane: str | None = None,
) -> CoherenceExecuteResult:
    """Execute-path coherence checks for capability bridge policy caps."""
    if not fabric_genes_aligned:
        return CoherenceExecuteResult(
            allowed=False,
            reason="coherence fabric misaligned",
        )
    if not _is_policy_capability(capability_id, lane_resolution):
        return CoherenceExecuteResult(allowed=True)
    if safety_halt:
        return CoherenceExecuteResult(
            allowed=False,
            reason="safety envelope halt",
        )
    mode = str(bridge_governance_mode or "strict").strip().lower()
    if mode != "strict":
        return CoherenceExecuteResult(
            allowed=False,
            reason="policy capability requires strict bridge governance_mode",
        )
    _ = authority_lane or build_operator_profile().get("authority_lane")
    return CoherenceExecuteResult(allowed=True)


def evaluate_pipeline_coherence(
    *,
    fabric_genes_aligned: bool,
    safety_halt: bool,
) -> CoherenceExecuteResult:
    """Pipeline-path coherence checks (no policy-cap / strict-mode branch)."""
    if not fabric_genes_aligned:
        return CoherenceExecuteResult(
            allowed=False,
            reason="coherence fabric misaligned",
        )
    if safety_halt:
        return CoherenceExecuteResult(
            allowed=False,
            reason="safety envelope halt",
        )
    return CoherenceExecuteResult(allowed=True)


def coherence_hard_block_enabled() -> bool:
    """Env gate for cognitive-path hard block (default on)."""
    raw = os.environ.get("AAIS_COHERENCE_HARD_BLOCK", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def coherence_protocol_from_pipeline(
    pipeline: dict[str, Any] | None,
) -> dict[str, str]:
    """Normalize coherence_protocol from a governed pipeline trace."""
    protocol = dict((pipeline or {}).get("coherence_protocol") or {})
    response = str(protocol.get("response") or "ALLOW").strip().upper()
    if response not in {"ALLOW", "BLOCK"}:
        response = "ALLOW"
    reason = _clip(protocol.get("reason"), 160) if response == "BLOCK" else ""
    return {"response": response, "reason": reason}


def assert_coherence_allows_turn(
    pipeline: dict[str, Any] | None,
) -> CoherenceExecuteResult:
    """Return whether a cognitive turn may proceed given pipeline coherence_protocol."""
    if not coherence_hard_block_enabled():
        return CoherenceExecuteResult(allowed=True)
    protocol = coherence_protocol_from_pipeline(pipeline)
    if protocol["response"] == "BLOCK":
        return CoherenceExecuteResult(
            allowed=False,
            reason=protocol["reason"] or "coherence fabric blocked",
        )
    return CoherenceExecuteResult(allowed=True)


def coherence_inputs_for_bridge(
    bridge_snapshot: dict[str, Any],
    *,
    root: Path | None = None,
    gene: str | None = None,
) -> tuple[str, LaneResolution, bool, bool]:
    """Derive bridge governance mode, lane resolution, fabric alignment, and safety halt."""
    root = _root(root)
    profile = build_operator_profile()
    authority_lane = str(profile.get("authority_lane") or "operator")
    bridge_env = to_bridge_envelope(bridge_snapshot)
    governance_mode = str(bridge_env.get("governance_mode") or "strict")
    lane_resolution = resolve_lane_for_gene(
        gene or "adaptive_lane_organ",
        root=root,
        authority_lane=authority_lane,
    )
    safety_status = build_envelope_status(root=root)
    safety_halt = bool((safety_status.get("thresholds") or {}).get("halt_required"))
    return governance_mode, lane_resolution, _fabric_genes_aligned(root), safety_halt


def _root(root: Path | None) -> Path:
    return root or repo_root()


def _idle_bridge_snapshot() -> dict[str, Any]:
    return {
        "bridge_id": "capability_service_bridge",
        "version": "1",
        "phase_gate": {
            "bridge": {
                "governance_mode": "strict",
                "runtime_context": "operator_runtime",
            }
        },
        "recent_events": [],
    }


def _idle_pipeline_baseline() -> dict[str, Any]:
    return {
        "pipeline_id": PIPELINE_ID,
        "version": PIPELINE_VERSION,
        "active_lane": DIRECT_COGNITIVE_LANE,
        "realtime_signal_feed": {"risk_level": "low", "system_state": "idle"},
        "immune_protocol": {"response": "ALLOW"},
    }


def _fabric_genes_aligned(root: Path) -> bool:
    import importlib.util

    script = root / "tools/governance/check_alt6_governed_eligibility.py"
    spec = importlib.util.spec_from_file_location("check_alt6_governed_eligibility", script)
    if spec is None or spec.loader is None:
        return False
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return not module.check_eligibility(root)


def _build_runtime_posture() -> list[dict[str, str]]:
    from src.memory_runtime_organ import build_memory_runtime_status
    from src.reflection_runtime_organ import build_reflection_runtime_status

    posture: list[dict[str, str]] = []
    for organ_id, builder in (
        ("reflection_runtime_organ", build_reflection_runtime_status),
        ("memory_runtime_organ", build_memory_runtime_status),
    ):
        status = builder()
        posture.append(
            {
                "organ_id": organ_id,
                "stage": str(status.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
                "claim_label": str(status.get("claim_label") or "asserted")[:32],
            }
        )
    return posture


def _build_mind_posture(
    *,
    pipeline_trace: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    from src.continuity_witness_organ import build_continuity_witness_status
    from src.intent_agency_organ import build_intent_agency_status
    from src.narrative_continuity_organ import build_narrative_continuity_status

    posture: list[dict[str, Any]] = []
    witness = build_continuity_witness_status(governed_pipeline=pipeline_trace)
    posture.append(
        {
            "organ_id": "continuity_witness_organ",
            "stage": str(witness.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(witness.get("claim_label") or "asserted")[:32],
            "drift_band": str(witness.get("drift_band") or "idle")[:32],
        }
    )
    narrative = build_narrative_continuity_status()
    posture.append(
        {
            "organ_id": "narrative_continuity_organ",
            "stage": str(narrative.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(narrative.get("claim_label") or "asserted")[:32],
            "continuity_score": float(narrative.get("continuity_score") or 0.0),
        }
    )
    intent = build_intent_agency_status()
    posture.append(
        {
            "organ_id": "intent_agency_organ",
            "stage": str(intent.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(intent.get("claim_label") or "asserted")[:32],
            "agency_claim_posture": str(intent.get("agency_claim_posture") or "asserted")[:32],
        }
    )
    return posture


def _mind_planes_aligned(mind_posture: list[dict[str, Any]]) -> bool:
    if len(mind_posture) < 3:
        return False
    for item in mind_posture:
        if str(item.get("drift_band") or "") == "critical":
            return False
        if str(item.get("claim_label") or "") == "rejected":
            return False
    return True


def _build_infrastructure_posture(
    *,
    pipeline_trace: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    from src.invariant_engine_organ import build_invariant_engine_status
    from src.phase_gate_organ import build_phase_gate_status
    from src.realtime_event_cause_predictor_organ import build_realtime_predictor_status

    posture: list[dict[str, Any]] = []
    phase = build_phase_gate_status()
    posture.append(
        {
            "organ_id": "phase_gate_organ",
            "stage": str(phase.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(phase.get("claim_label") or "asserted")[:32],
            "producer_attested": False,
            "consumer_attested": False,
        }
    )
    predictor = build_realtime_predictor_status(governed_pipeline=pipeline_trace)
    posture.append(
        {
            "organ_id": "realtime_event_cause_predictor_organ",
            "stage": str(predictor.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(predictor.get("claim_label") or "asserted")[:32],
            "producer_attested": bool(predictor.get("live_runtime_producer")),
            "consumer_attested": False,
        }
    )
    invariant = build_invariant_engine_status(governed_pipeline=pipeline_trace)
    posture.append(
        {
            "organ_id": "invariant_engine_organ",
            "stage": str(invariant.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(invariant.get("claim_label") or "asserted")[:32],
            "producer_attested": False,
            "consumer_attested": bool(invariant.get("nova_runtime_consumer")),
        }
    )
    return posture


def _infrastructure_substrate_aligned(infrastructure_posture: list[dict[str, Any]]) -> bool:
    if len(infrastructure_posture) < 3:
        return False
    producer_ok = any(item.get("producer_attested") for item in infrastructure_posture)
    consumer_ok = any(item.get("consumer_attested") for item in infrastructure_posture)
    for item in infrastructure_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
    return producer_ok and consumer_ok


def _build_memory_governance_posture() -> list[dict[str, Any]]:
    from src.knowledge_authority_organ import build_knowledge_authority_status
    from src.memory_path_governance_organ import build_memory_path_governance_status
    from src.verification_gate_organ import build_verification_gate_status

    posture: list[dict[str, Any]] = []
    for organ_id, builder in (
        ("verification_gate_organ", build_verification_gate_status),
        ("memory_path_governance_organ", build_memory_path_governance_status),
        ("knowledge_authority_organ", build_knowledge_authority_status),
    ):
        status = builder()
        posture.append(
            {
                "organ_id": organ_id,
                "stage": str(status.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
                "claim_label": str(status.get("claim_label") or "asserted")[:32],
                "paths_documented": organ_id == "memory_path_governance_organ",
            }
        )
    return posture


def _memory_paths_aligned(memory_posture: list[dict[str, Any]]) -> bool:
    if len(memory_posture) < 3:
        return False
    for item in memory_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
    return True


def _build_forensics_posture() -> list[dict[str, Any]]:
    from src.forensic_triangulation_organ import build_forensic_triangulation_status
    from src.mechanic_handoff_organ import build_mechanic_handoff_status
    from src.scorpion_bridge_organ import build_scorpion_bridge_status

    posture: list[dict[str, Any]] = []
    scorpion = build_scorpion_bridge_status()
    posture.append(
        {
            "organ_id": "scorpion_bridge_organ",
            "stage": str(scorpion.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(scorpion.get("claim_label") or "asserted")[:32],
            "handoff_attested": bool(scorpion.get("scorpion_claim_label")),
        }
    )
    mechanic = build_mechanic_handoff_status()
    posture.append(
        {
            "organ_id": "mechanic_handoff_organ",
            "stage": str(mechanic.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(mechanic.get("claim_label") or "asserted")[:32],
            "handoff_attested": True,
        }
    )
    tri = build_forensic_triangulation_status()
    posture.append(
        {
            "organ_id": "forensic_triangulation_organ",
            "stage": str(tri.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(tri.get("claim_label") or "asserted")[:32],
            "handoff_attested": bool(tri.get("triangulation_package_present")),
        }
    )
    return posture


def _forensics_handoff_aligned(forensics_posture: list[dict[str, Any]]) -> bool:
    if len(forensics_posture) < 3:
        return False
    for item in forensics_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("handoff_attested"):
            return False
    return True


def _build_immune_observe_posture(
    *,
    pipeline_trace: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    from src.immune_observe_organ import build_immune_observe_status
    from src.policy_gate_organ import build_policy_gate_status
    from src.predictor_immune_bridge_organ import build_predictor_immune_bridge_status

    posture: list[dict[str, Any]] = []
    immune = build_immune_observe_status()
    posture.append(
        {
            "organ_id": "immune_observe_organ",
            "stage": str(immune.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(immune.get("claim_label") or "asserted")[:32],
            "observe_only": bool(immune.get("observe_protocol_only")),
            "substrate_bridged": False,
        }
    )
    policy = build_policy_gate_status()
    posture.append(
        {
            "organ_id": "policy_gate_organ",
            "stage": str(policy.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(policy.get("claim_label") or "asserted")[:32],
            "observe_only": bool(policy.get("observe_protocol_only")),
            "substrate_bridged": False,
        }
    )
    bridge = build_predictor_immune_bridge_status(governed_pipeline=pipeline_trace)
    posture.append(
        {
            "organ_id": "predictor_immune_bridge_organ",
            "stage": str(bridge.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(bridge.get("claim_label") or "asserted")[:32],
            "observe_only": bool(bridge.get("immune_observe_only")),
            "substrate_bridged": bool(bridge.get("substrate_bridged")),
        }
    )
    return posture


def _immune_observe_aligned(
    immune_posture: list[dict[str, Any]],
    *,
    require_bridge: bool = False,
) -> bool:
    if len(immune_posture) < 3:
        return False
    bridged = False
    for item in immune_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("observe_only"):
            return False
        if item.get("substrate_bridged"):
            bridged = True
    if require_bridge:
        return bridged
    return True


def _build_authority_trace_posture() -> list[dict[str, Any]]:
    from src.cognitive_bridge_organ import build_cognitive_bridge_status
    from src.governed_event_chain_organ import build_governed_event_chain_status
    from src.tracing_spine_organ import build_tracing_spine_status

    posture: list[dict[str, Any]] = []
    for organ_id, builder in (
        ("cognitive_bridge_organ", build_cognitive_bridge_status),
        ("governed_event_chain_organ", build_governed_event_chain_status),
        ("tracing_spine_organ", build_tracing_spine_status),
    ):
        status = builder()
        trace_attested = organ_id != "tracing_spine_organ" or bool(
            status.get("canonical_stages_present")
        )
        posture.append(
            {
                "organ_id": organ_id,
                "stage": str(status.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
                "claim_label": str(status.get("claim_label") or "asserted")[:32],
                "trace_attested": trace_attested,
            }
        )
    return posture


def _authority_trace_aligned(authority_trace_posture: list[dict[str, Any]]) -> bool:
    if len(authority_trace_posture) < 3:
        return False
    for item in authority_trace_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("trace_attested"):
            return False
    return True


def _build_mission_boundary_posture() -> list[dict[str, Any]]:
    from src.aris_boundary_organ import build_aris_boundary_status
    from src.capability_module_organ import build_capability_module_status
    from src.mission_board_organ import build_mission_board_status

    posture: list[dict[str, Any]] = []
    mission = build_mission_board_status()
    posture.append(
        {
            "organ_id": "mission_board_organ",
            "stage": str(mission.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(mission.get("claim_label") or "asserted")[:32],
            "boundary_attested": mission.get("verification_gate_decision") is not None,
        }
    )
    aris = build_aris_boundary_status()
    posture.append(
        {
            "organ_id": "aris_boundary_organ",
            "stage": str(aris.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(aris.get("claim_label") or "asserted")[:32],
            "boundary_attested": bool(aris.get("non_copy_allowed")),
        }
    )
    cap = build_capability_module_status()
    posture.append(
        {
            "organ_id": "capability_module_organ",
            "stage": str(cap.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(cap.get("claim_label") or "asserted")[:32],
            "boundary_attested": bool(cap.get("capability_module_present")),
        }
    )
    return posture


def _mission_boundary_aligned(mission_boundary_posture: list[dict[str, Any]]) -> bool:
    if len(mission_boundary_posture) < 3:
        return False
    for item in mission_boundary_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("boundary_attested"):
            return False
    return True


def _build_coding_posture() -> list[dict[str, Any]]:
    from src.change_scope_organ import build_change_scope_status
    from src.patch_verification_organ import build_patch_verification_status
    from src.patchforge_organ import build_patchforge_status

    posture: list[dict[str, Any]] = []
    pf = build_patchforge_status()
    posture.append(
        {
            "organ_id": "patchforge_organ",
            "stage": str(pf.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(pf.get("claim_label") or "asserted")[:32],
            "proposal_only": bool(pf.get("proposal_only")),
        }
    )
    cs = build_change_scope_status()
    posture.append(
        {
            "organ_id": "change_scope_organ",
            "stage": str(cs.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(cs.get("claim_label") or "asserted")[:32],
            "proposal_only": True,
        }
    )
    pv = build_patch_verification_status()
    posture.append(
        {
            "organ_id": "patch_verification_organ",
            "stage": str(pv.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(pv.get("claim_label") or "asserted")[:32],
            "proposal_only": not bool(pv.get("silent_apply_allowed")),
        }
    )
    return posture


def _coding_stack_aligned(coding_posture: list[dict[str, Any]]) -> bool:
    if len(coding_posture) < 3:
        return False
    for item in coding_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("proposal_only"):
            return False
    return True


def _build_otem_lane_posture() -> list[dict[str, Any]]:
    from src.direct_challenge_organ import build_direct_challenge_status
    from src.orchestration_spine_organ import build_orchestration_spine_status
    from src.otem_bounded_organ import build_otem_bounded_status

    posture: list[dict[str, Any]] = []
    otem = build_otem_bounded_status()
    posture.append(
        {
            "organ_id": "otem_bounded_organ",
            "stage": str(otem.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(otem.get("claim_label") or "asserted")[:32],
            "proposal_only": bool(otem.get("proposal_only")),
        }
    )
    dc = build_direct_challenge_status()
    posture.append(
        {
            "organ_id": "direct_challenge_organ",
            "stage": str(dc.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(dc.get("claim_label") or "asserted")[:32],
            "proposal_only": True,
        }
    )
    spine = build_orchestration_spine_status()
    posture.append(
        {
            "organ_id": "orchestration_spine_organ",
            "stage": str(spine.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(spine.get("claim_label") or "asserted")[:32],
            "proposal_only": bool(spine.get("routing_read_only")),
        }
    )
    return posture


def _otem_lane_aligned(otem_lane_posture: list[dict[str, Any]]) -> bool:
    if len(otem_lane_posture) < 3:
        return False
    for item in otem_lane_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("proposal_only"):
            return False
    return True


def _build_predictive_lane_posture(
    *,
    pipeline_trace: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    from src.governed_realtime_lane_organ import build_governed_realtime_lane_status
    from src.operator_health_sentinel_organ import build_operator_health_sentinel_organ_status
    from src.v8_runtime_organ import build_v8_runtime_status

    posture: list[dict[str, Any]] = []
    sentinel = build_operator_health_sentinel_organ_status()
    posture.append(
        {
            "organ_id": "operator_health_sentinel_organ",
            "stage": str(sentinel.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(sentinel.get("claim_label") or "asserted")[:32],
            "advisory_only": bool(sentinel.get("advisory_only")),
        }
    )
    lane = build_governed_realtime_lane_status(governed_pipeline=pipeline_trace)
    posture.append(
        {
            "organ_id": "governed_realtime_lane_organ",
            "stage": str(lane.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(lane.get("claim_label") or "asserted")[:32],
            "advisory_only": True,
        }
    )
    v8 = build_v8_runtime_status()
    posture.append(
        {
            "organ_id": "v8_runtime_organ",
            "stage": str(v8.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(v8.get("claim_label") or "asserted")[:32],
            "advisory_only": True,
        }
    )
    return posture


def _predictive_lane_aligned(predictive_lane_posture: list[dict[str, Any]]) -> bool:
    if len(predictive_lane_posture) < 3:
        return False
    for item in predictive_lane_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("advisory_only"):
            return False
    return True


def _build_execution_depth_posture() -> list[dict[str, Any]]:
    from src.patch_apply_organ import build_patch_apply_status
    from src.patch_execution_preview_organ import build_patch_execution_preview_status
    from src.run_ledger_organ import build_run_ledger_status

    posture: list[dict[str, Any]] = []
    apply_status = build_patch_apply_status()
    posture.append(
        {
            "organ_id": "patch_apply_organ",
            "stage": str(apply_status.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(apply_status.get("claim_label") or "asserted")[:32],
            "operator_gated": bool(apply_status.get("operator_gated")),
        }
    )
    preview = build_patch_execution_preview_status()
    posture.append(
        {
            "organ_id": "patch_execution_preview_organ",
            "stage": str(preview.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(preview.get("claim_label") or "asserted")[:32],
            "operator_gated": True,
        }
    )
    ledger = build_run_ledger_status()
    posture.append(
        {
            "organ_id": "run_ledger_organ",
            "stage": str(ledger.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(ledger.get("claim_label") or "asserted")[:32],
            "operator_gated": True,
        }
    )
    return posture


def _execution_depth_aligned(execution_depth_posture: list[dict[str, Any]]) -> bool:
    if len(execution_depth_posture) < 3:
        return False
    for item in execution_depth_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("operator_gated"):
            return False
    return True


def _build_constitutional_creative_posture() -> list[dict[str, Any]]:
    from src.human_voice_extraction_organ import build_human_voice_extraction_status
    from src.imagine_generator_organ import build_imagine_generator_status
    from src.narrative_trust_pack_organ import build_narrative_trust_pack_status
    from src.recipe_module_organ import build_recipe_module_status
    from src.ul_lineage_console_organ import build_ul_lineage_console_status

    posture: list[dict[str, Any]] = []
    for organ_id, builder in (
        ("ul_lineage_console_organ", build_ul_lineage_console_status),
        ("recipe_module_organ", build_recipe_module_status),
        ("imagine_generator_organ", build_imagine_generator_status),
        ("human_voice_extraction_organ", build_human_voice_extraction_status),
        ("narrative_trust_pack_organ", build_narrative_trust_pack_status),
    ):
        snap = builder()
        posture.append(
            {
                "organ_id": organ_id,
                "stage": str(snap.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
                "claim_label": str(snap.get("claim_label") or "asserted")[:32],
                "bridge_safe": bool(snap.get("bridge_safe")),
                "proposal_only": bool(snap.get("proposal_only")),
            }
        )
    return posture


def _constitutional_creative_aligned(
    constitutional_creative_posture: list[dict[str, Any]],
) -> bool:
    if len(constitutional_creative_posture) < 5:
        return False
    for item in constitutional_creative_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("bridge_safe"):
            return False
        if not item.get("proposal_only"):
            return False
    return True


def _build_story_chain_posture() -> list[dict[str, Any]]:
    from src.beatbox_lane_organ import build_beatbox_lane_status
    from src.speakers_lane_organ import build_speakers_lane_status
    from src.story_forge_lane_organ import build_story_forge_lane_status

    posture: list[dict[str, Any]] = []
    for organ_id, builder, signoff in (
        ("story_forge_lane_organ", build_story_forge_lane_status, False),
        ("beatbox_lane_organ", build_beatbox_lane_status, False),
        ("speakers_lane_organ", build_speakers_lane_status, False),
    ):
        snap = builder()
        posture.append(
            {
                "organ_id": organ_id,
                "stage": str(snap.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
                "claim_label": str(snap.get("claim_label") or "asserted")[:32],
                "bridge_safe": bool(snap.get("bridge_safe")),
                "signoff_required": signoff,
            }
        )
    return posture


def _story_chain_aligned(story_chain_posture: list[dict[str, Any]]) -> bool:
    if len(story_chain_posture) < 3:
        return False
    for item in story_chain_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("bridge_safe"):
            return False
    return True


def _build_module_governance_posture() -> list[dict[str, Any]]:
    from src.module_governance_organ import build_module_governance_status

    snap = build_module_governance_status()
    return [
        {
            "organ_id": "module_governance_organ",
            "stage": str(snap.get("cisiv_stage") or "implementation")[:MAX_FIELD_LEN],
            "claim_label": str(snap.get("claim_label") or "asserted")[:32],
            "major_violation_disable_module": bool(snap.get("major_violation_disable_module")),
        }
    ]


def _module_governance_aligned(module_governance_posture: list[dict[str, Any]]) -> bool:
    if len(module_governance_posture) < 1:
        return False
    item = module_governance_posture[0]
    if str(item.get("claim_label") or "") == "rejected":
        return False
    return bool(item.get("major_violation_disable_module"))


def _organ_posture_item(organ_id: str, snap: dict[str, Any], **extra: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "organ_id": organ_id,
        "stage": str(snap.get("cisiv_stage") or "implementation"),
        "claim_label": str(snap.get("claim_label") or "asserted"),
    }
    item.update(extra)
    return item


def _build_perception_posture() -> list[dict[str, Any]]:
    from src.document_vision_organ import build_document_vision_status
    from src.perception_gateway_organ import build_perception_gateway_status
    from src.ui_vision_organ import build_ui_vision_status

    doc = build_document_vision_status()
    ui = build_ui_vision_status()
    gateway = build_perception_gateway_status()
    return [
        _organ_posture_item(
            "document_vision_organ",
            doc,
            bridge_safe=bool(doc.get("bridge_safe")),
            env_gated=True,
        ),
        _organ_posture_item(
            "ui_vision_organ",
            ui,
            bridge_safe=bool(ui.get("bridge_safe")),
            env_gated=True,
        ),
        _organ_posture_item(
            "perception_gateway_organ",
            gateway,
            bridge_safe=bool(gateway.get("bridge_safe")),
            env_gated=True,
        ),
    ]


def _perception_aligned(perception_posture: list[dict[str, Any]]) -> bool:
    if len(perception_posture) < 3:
        return False
    for item in perception_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("bridge_safe"):
            return False
    return True


def _build_spatial_symbolic_posture() -> list[dict[str, Any]]:
    from src.mystic_engine_organ import build_mystic_engine_status
    from src.perception_lane_organ import build_perception_lane_status
    from src.spatial_reasoning_organ import build_spatial_reasoning_status

    spatial = build_spatial_reasoning_status()
    mystic = build_mystic_engine_status()
    lane = build_perception_lane_status()
    return [
        _organ_posture_item(
            "spatial_reasoning_organ",
            spatial,
            bridge_safe=bool(spatial.get("bridge_safe")),
            operator_gated=bool(spatial.get("operator_gated")),
        ),
        _organ_posture_item(
            "mystic_engine_organ",
            mystic,
            bridge_safe=bool(mystic.get("bridge_safe")),
            operator_gated=bool(mystic.get("operator_gated")),
        ),
        _organ_posture_item(
            "perception_lane_organ",
            lane,
            bridge_safe=bool(lane.get("bridge_safe")),
            operator_gated=bool(lane.get("operator_gated")),
        ),
    ]


def _spatial_symbolic_aligned(spatial_symbolic_posture: list[dict[str, Any]]) -> bool:
    if len(spatial_symbolic_posture) < 3:
        return False
    for item in spatial_symbolic_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("bridge_safe") or not item.get("operator_gated"):
            return False
    return True


def _build_route_choice_posture() -> list[dict[str, Any]]:
    from src.provider_route_organ import build_provider_route_status
    from src.route_choice_organ import build_route_choice_status
    from src.specialist_route_organ import build_specialist_route_status

    route = build_route_choice_status()
    specialist = build_specialist_route_status()
    provider = build_provider_route_status()
    return [
        _organ_posture_item(
            "route_choice_organ",
            route,
            advisory_only=bool(route.get("advisory_only")),
            routing_read_only=bool(route.get("routing_read_only")),
        ),
        _organ_posture_item(
            "specialist_route_organ",
            specialist,
            advisory_only=bool(specialist.get("advisory_only")),
            routing_read_only=bool(specialist.get("routing_read_only")),
        ),
        _organ_posture_item(
            "provider_route_organ",
            provider,
            advisory_only=bool(provider.get("advisory_only")),
            routing_read_only=bool(provider.get("routing_read_only")),
        ),
    ]


def _route_choice_aligned(route_choice_posture: list[dict[str, Any]]) -> bool:
    if len(route_choice_posture) < 3:
        return False
    for item in route_choice_posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("advisory_only") or not item.get("routing_read_only"):
            return False
    return True


def _build_executive_attention_posture() -> list[dict[str, Any]]:
    from src.attention_organ import build_attention_status
    from src.coherence_projection_organ import build_coherence_projection_status
    from src.reasoning_executive_organ import build_reasoning_executive_status

    reasoning = build_reasoning_executive_status()
    attention = build_attention_status()
    projection = build_coherence_projection_status()
    return [
        _organ_posture_item(
            "reasoning_executive_organ",
            reasoning,
            read_only=bool(reasoning.get("read_only")),
            routing_usurpation=bool(reasoning.get("routing_usurpation")),
        ),
        _organ_posture_item(
            "attention_organ",
            attention,
            read_only=bool(attention.get("read_only")),
        ),
        _organ_posture_item(
            "coherence_projection_organ",
            projection,
            read_only=bool(projection.get("read_only")),
            exports_bounded_state=bool(projection.get("exports_bounded_state")),
        ),
    ]


def _executive_attention_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 3:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("read_only"):
            return False
        if item.get("organ_id") == "reasoning_executive_organ" and item.get(
            "routing_usurpation"
        ):
            return False
    return True


def _build_deliberation_planning_posture() -> list[dict[str, Any]]:
    from src.cortex_arcs_organ import build_cortex_arcs_status
    from src.deliberation_organ import build_deliberation_status
    from src.planning_organ import build_planning_status

    deliberation = build_deliberation_status()
    planning = build_planning_status()
    arcs = build_cortex_arcs_status()
    return [
        _organ_posture_item(
            "deliberation_organ",
            deliberation,
            read_only=bool(deliberation.get("read_only")),
        ),
        _organ_posture_item(
            "planning_organ",
            planning,
            read_only=bool(planning.get("read_only")),
        ),
        _organ_posture_item(
            "cortex_arcs_organ",
            arcs,
            read_only=bool(arcs.get("read_only")),
        ),
    ]


def _deliberation_planning_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 3:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("read_only"):
            return False
    return True


def _build_voice_execution_posture() -> list[dict[str, Any]]:
    from src.cognitive_execution_organ import build_cognitive_execution_status
    from src.nova_face_organ import build_nova_face_status
    from src.speaking_runtime_organ import build_speaking_runtime_status

    execution = build_cognitive_execution_status()
    speaking = build_speaking_runtime_status()
    face = build_nova_face_status()
    return [
        _organ_posture_item(
            "cognitive_execution_organ",
            execution,
            read_only=bool(execution.get("read_only")),
            patch_execution_depth=bool(execution.get("patch_execution_depth")),
        ),
        _organ_posture_item(
            "speaking_runtime_organ",
            speaking,
            read_only=bool(speaking.get("read_only")),
        ),
        _organ_posture_item(
            "nova_face_organ",
            face,
            read_only=bool(face.get("read_only")),
            authority_lane=str(face.get("authority_lane") or ""),
        ),
    ]


def _voice_execution_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 3:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("read_only"):
            return False
        if item.get("organ_id") == "cognitive_execution_organ" and item.get(
            "patch_execution_depth"
        ):
            return False
        if item.get("organ_id") == "nova_face_organ" and str(
            item.get("authority_lane") or ""
        ) != "jarvis":
            return False
    return True


def _build_factory_fabrication_posture() -> list[dict[str, Any]]:
    from src.ai_factory_organ import build_ai_factory_status
    from src.cogos_runtime_bridge_organ import build_cogos_runtime_bridge_status
    from src.wolf_rehydration_organ import build_wolf_rehydration_status

    factory = build_ai_factory_status()
    bridge = build_cogos_runtime_bridge_status()
    wolf = build_wolf_rehydration_status()
    return [
        _organ_posture_item(
            "ai_factory_organ",
            factory,
            read_only=bool(factory.get("read_only")),
            deploy_authority_via_organ=bool(
                factory.get("deploy_authority_via_organ")
            ),
        ),
        _organ_posture_item(
            "cogos_runtime_bridge_organ",
            bridge,
            read_only=bool(bridge.get("read_only")),
            family_valid=bool(bridge.get("family_valid")),
        ),
        _organ_posture_item(
            "wolf_rehydration_organ",
            wolf,
            read_only=bool(wolf.get("read_only")),
        ),
    ]


def _factory_fabrication_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 3:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if not item.get("read_only"):
            return False
        if item.get("organ_id") == "ai_factory_organ" and item.get(
            "deploy_authority_via_organ"
        ):
            return False
    return True


def _build_contractor_lane_posture() -> list[dict[str, Any]]:
    from src.evolve_engine_organ import build_evolve_engine_status
    from src.forge_contractor_organ import build_forge_contractor_status
    from src.forge_eval_organ import build_forge_eval_status

    forge = build_forge_contractor_status()
    eval_lane = build_forge_eval_status()
    evolve = build_evolve_engine_status()
    return [
        _organ_posture_item(
            "forge_contractor_organ",
            forge,
            proposal_only=bool(forge.get("proposal_only")),
        ),
        _organ_posture_item(
            "forge_eval_organ",
            eval_lane,
            read_only=bool(eval_lane.get("read_only")),
        ),
        _organ_posture_item(
            "evolve_engine_organ",
            evolve,
            special_review_only=bool(evolve.get("special_review_only")),
            direct_patch_authority=bool(evolve.get("direct_patch_authority")),
        ),
    ]


def _contractor_lanes_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 3:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if item.get("organ_id") == "forge_contractor_organ" and not item.get(
            "proposal_only"
        ):
            return False
        if item.get("organ_id") == "evolve_engine_organ" and item.get(
            "direct_patch_authority"
        ):
            return False
    return True


def _build_kinetic_shell_posture() -> list[dict[str, Any]]:
    from src.operator_workbench_organ import build_operator_workbench_status
    from src.slingshot_organ import build_slingshot_status
    from src.workflow_shell_organ import build_workflow_shell_status

    slingshot = build_slingshot_status()
    workbench = build_operator_workbench_status()
    shell = build_workflow_shell_status()
    return [
        _organ_posture_item(
            "slingshot_organ",
            slingshot,
            read_only=bool(slingshot.get("read_only")),
            ma13_enforced=bool(slingshot.get("ma13_enforced")),
        ),
        _organ_posture_item(
            "operator_workbench_organ",
            workbench,
            proposal_only=bool(workbench.get("proposal_only")),
        ),
        _organ_posture_item(
            "workflow_shell_organ",
            shell,
            read_only=bool(shell.get("read_only")),
        ),
    ]


def _kinetic_shell_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 3:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if item.get("organ_id") == "operator_workbench_organ" and not item.get(
            "proposal_only"
        ):
            return False
        if item.get("organ_id") == "slingshot_organ" and not item.get("ma13_enforced"):
            return False
    return True


def _build_protocol_posture() -> list[dict[str, Any]]:
    from src.jarvis_protocol_organ import build_jarvis_protocol_status
    from src.jarvis_reasoning_lane_organ import build_jarvis_reasoning_lane_status
    from src.reasoning_contract_organ import build_reasoning_contract_status

    protocol = build_jarvis_protocol_status()
    contract = build_reasoning_contract_status()
    lane = build_jarvis_reasoning_lane_status()
    return [
        _organ_posture_item(
            "jarvis_protocol_organ",
            protocol,
            read_only=bool(protocol.get("read_only")),
        ),
        _organ_posture_item(
            "reasoning_contract_organ",
            contract,
            executive_usurpation=bool(contract.get("executive_usurpation")),
        ),
        _organ_posture_item(
            "jarvis_reasoning_lane_organ",
            lane,
            routing_usurpation=bool(lane.get("routing_usurpation")),
            lane_catalog_only=bool(lane.get("lane_catalog_only")),
        ),
    ]


def _protocol_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 3:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if item.get("organ_id") == "reasoning_contract_organ" and item.get(
            "executive_usurpation"
        ):
            return False
        if item.get("organ_id") == "jarvis_reasoning_lane_organ" and item.get(
            "routing_usurpation"
        ):
            return False
    return True


def _build_authority_shell_posture() -> list[dict[str, Any]]:
    from src.continuity_substrate_organ import build_continuity_substrate_status
    from src.conversation_memory_organ import build_conversation_memory_status
    from src.jarvis_operator_organ import build_jarvis_operator_status

    memory = build_conversation_memory_status()
    continuity = build_continuity_substrate_status()
    operator = build_jarvis_operator_status()
    return [
        _organ_posture_item(
            "conversation_memory_organ",
            memory,
            read_only=bool(memory.get("read_only")),
        ),
        _organ_posture_item(
            "continuity_substrate_organ",
            continuity,
            substrate_aligned=bool(continuity.get("substrate_aligned")),
        ),
        _organ_posture_item(
            "jarvis_operator_organ",
            operator,
            new_execute_authority_via_organ=bool(
                operator.get("new_execute_authority_via_organ")
            ),
        ),
    ]


def _authority_shell_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 3:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if item.get("organ_id") == "jarvis_operator_organ" and item.get(
            "new_execute_authority_via_organ"
        ):
            return False
        if item.get("organ_id") == "continuity_substrate_organ" and not item.get(
            "substrate_aligned"
        ):
            return False
    return True


def _build_response_integrity_posture() -> list[dict[str, Any]]:
    from src.anti_drift_organ import build_anti_drift_status
    from src.output_integrity_organ import build_output_integrity_status
    from src.prompt_assembly_organ import build_prompt_assembly_status

    anti = build_anti_drift_status()
    prompt = build_prompt_assembly_status()
    output = build_output_integrity_status()
    return [
        _organ_posture_item(
            "anti_drift_organ",
            anti,
            read_only=bool(anti.get("read_only")),
            thread_contract_active=bool(anti.get("thread_contract_active")),
        ),
        _organ_posture_item(
            "prompt_assembly_organ",
            prompt,
            scaffold_suppression=bool(prompt.get("scaffold_suppression")),
        ),
        _organ_posture_item(
            "output_integrity_organ",
            output,
            finalization_read_only=bool(output.get("finalization_read_only")),
        ),
    ]


def _response_integrity_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 3:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if item.get("organ_id") == "output_integrity_organ" and not item.get(
            "finalization_read_only"
        ):
            return False
    return True


def _build_law_cycle_posture() -> list[dict[str, Any]]:
    from src.project_infi_law_organ import build_project_infi_law_status
    from src.project_infi_state_machine_organ import build_project_infi_state_machine_status
    from src.run_ledger_binding_organ import build_run_ledger_binding_status

    sm = build_project_infi_state_machine_status()
    law = build_project_infi_law_status()
    bind = build_run_ledger_binding_status()
    return [
        _organ_posture_item(
            "project_infi_state_machine_organ",
            sm,
            special_review_only=bool(sm.get("special_review_only")),
        ),
        _organ_posture_item(
            "project_infi_law_organ",
            law,
            autonomous_law_mutation=bool(law.get("autonomous_law_mutation")),
        ),
        _organ_posture_item("run_ledger_binding_organ", bind),
    ]


def _law_cycle_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 3:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if item.get("organ_id") == "project_infi_law_organ" and item.get(
            "autonomous_law_mutation"
        ):
            return False
    return True


def _build_turn_admission_posture() -> list[dict[str, Any]]:
    from src.aais_ul_substrate_organ import build_aais_ul_substrate_status
    from src.aris_integration_organ import build_aris_integration_status
    from src.chat_turn_governance_organ import build_chat_turn_governance_status

    chat = build_chat_turn_governance_status()
    ul = build_aais_ul_substrate_status()
    aris = build_aris_integration_status()
    return [
        _organ_posture_item("chat_turn_governance_organ", chat),
        _organ_posture_item("aais_ul_substrate_organ", ul),
        _organ_posture_item("aris_integration_organ", aris),
    ]


def _turn_admission_aligned(posture: list[dict[str, Any]]) -> bool:
    return len(posture) >= 3 and all(
        str(item.get("claim_label") or "") != "rejected" for item in posture
    )


def _build_governance_control_posture() -> list[dict[str, Any]]:
    from src.governance_layer_organ import build_governance_layer_status
    from src.security_protocol_organ import build_security_protocol_status
    from src.system_guard_organ import build_system_guard_status

    gov = build_governance_layer_status()
    sec = build_security_protocol_status()
    guard = build_system_guard_status()
    return [
        _organ_posture_item("governance_layer_organ", gov),
        _organ_posture_item(
            "security_protocol_organ",
            sec,
            security_protocol_core_present=bool(sec.get("security_protocol_core_present")),
        ),
        _organ_posture_item("system_guard_organ", guard),
    ]


def _governance_control_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 3:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if item.get("organ_id") == "security_protocol_organ" and not item.get(
            "security_protocol_core_present"
        ):
            return False
    return True


def _build_product_shell_posture() -> list[dict[str, Any]]:
    from src.aais_doctor_organ import build_aais_doctor_status
    from src.launcher_organ import build_launcher_status
    from src.workflow_runtime_organ import build_workflow_runtime_status

    return [
        _organ_posture_item("launcher_organ", build_launcher_status()),
        _organ_posture_item("aais_doctor_organ", build_aais_doctor_status()),
        _organ_posture_item("workflow_runtime_organ", build_workflow_runtime_status()),
    ]


def _product_shell_aligned(posture: list[dict[str, Any]]) -> bool:
    return len(posture) >= 3 and all(
        str(item.get("claim_label") or "") != "rejected" for item in posture
    )


def _build_operator_surface_posture() -> list[dict[str, Any]]:
    from src.dashboard_surface_organ import build_dashboard_surface_status
    from src.jarvis_console_surface_organ import build_jarvis_console_surface_status
    from src.memory_bank_surface_organ import build_memory_bank_surface_status
    from src.nova_landing_surface_organ import build_nova_landing_surface_status

    return [
        _organ_posture_item(
            "jarvis_console_surface_organ", build_jarvis_console_surface_status()
        ),
        _organ_posture_item(
            "memory_bank_surface_organ", build_memory_bank_surface_status()
        ),
        _organ_posture_item("dashboard_surface_organ", build_dashboard_surface_status()),
        _organ_posture_item(
            "nova_landing_surface_organ", build_nova_landing_surface_status()
        ),
    ]


def _operator_surface_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 4:
        return False
    return all(str(item.get("claim_label") or "") != "rejected" for item in posture)


def _build_composed_runtime_posture() -> list[dict[str, Any]]:
    from src.aais_composed_runtime_organ import build_aais_composed_runtime_status
    from src.api_gateway_organ import build_api_gateway_status

    gateway = build_api_gateway_status()
    return [
        _organ_posture_item(
            "aais_composed_runtime_organ", build_aais_composed_runtime_status()
        ),
        _organ_posture_item(
            "api_gateway_organ",
            gateway,
            ingress_read_only=bool(gateway.get("ingress_read_only")),
        ),
    ]


def _composed_runtime_aligned(posture: list[dict[str, Any]]) -> bool:
    if len(posture) < 2:
        return False
    for item in posture:
        if str(item.get("claim_label") or "") == "rejected":
            return False
        if item.get("organ_id") == "api_gateway_organ" and not item.get(
            "ingress_read_only"
        ):
            return False
    return True


def _layer_aligned(posture: list[dict[str, Any]], *, minimum: int) -> bool:
    if len(posture) < minimum:
        return False
    return all(str(item.get("claim_label") or "") != "rejected" for item in posture)


def _build_workspace_memory_layer() -> list[dict[str, Any]]:
    from src.jarvis_runs_organ import build_jarvis_runs_status
    from src.memory_smith_organ import build_memory_smith_status
    from src.operator_workspace_organ import build_operator_workspace_status

    return [
        _organ_posture_item("memory_smith_organ", build_memory_smith_status()),
        _organ_posture_item(
            "operator_workspace_organ", build_operator_workspace_status()
        ),
        _organ_posture_item("jarvis_runs_organ", build_jarvis_runs_status()),
    ]


def _build_hygiene_blueprint_layer() -> list[dict[str, Any]]:
    from src.blueprint_posture_organ import build_blueprint_posture_status
    from src.state_hygiene_organ import build_state_hygiene_status
    from src.workflow_interfaces_organ import build_workflow_interfaces_status

    return [
        _organ_posture_item("state_hygiene_organ", build_state_hygiene_status()),
        _organ_posture_item(
            "blueprint_posture_organ", build_blueprint_posture_status()
        ),
        _organ_posture_item(
            "workflow_interfaces_organ", build_workflow_interfaces_status()
        ),
    ]


def _build_extended_operator_interface_layer() -> list[dict[str, Any]]:
    from src.nova_workspace_interface_organ import (
        build_nova_workspace_interface_status,
    )
    from src.operator_console_interface_organ import (
        build_operator_console_interface_status,
    )
    from src.platform_console_interfaces_organ import (
        build_platform_console_interfaces_status,
    )

    return [
        _organ_posture_item(
            "platform_console_interfaces_organ",
            build_platform_console_interfaces_status(),
        ),
        _organ_posture_item(
            "operator_console_interface_organ",
            build_operator_console_interface_status(),
        ),
        _organ_posture_item(
            "nova_workspace_interface_organ",
            build_nova_workspace_interface_status(),
        ),
    ]


def _build_creative_core_layer() -> list[dict[str, Any]]:
    from src.creative_capability_bridge_organ import (
        build_creative_capability_bridge_status,
    )
    from src.creative_core_runtime_organ import build_creative_core_runtime_status
    from src.creative_operator_handoff_organ import (
        build_creative_operator_handoff_status,
    )

    return [
        _organ_posture_item(
            "creative_core_runtime_organ", build_creative_core_runtime_status()
        ),
        _organ_posture_item(
            "creative_capability_bridge_organ",
            build_creative_capability_bridge_status(),
        ),
        _organ_posture_item(
            "creative_operator_handoff_organ",
            build_creative_operator_handoff_status(),
        ),
    ]


def _build_v9_creative_layer() -> list[dict[str, Any]]:
    from src.creative_console_interface_organ import (
        build_creative_console_interface_status,
    )
    from src.v9_core_organ import build_v9_core_status
    from src.v9_runtime_organ import build_v9_runtime_status

    return [
        _organ_posture_item("v9_core_organ", build_v9_core_status()),
        _organ_posture_item("v9_runtime_organ", build_v9_runtime_status()),
        _organ_posture_item(
            "creative_console_interface_organ",
            build_creative_console_interface_status(),
        ),
    ]


def _build_v10_creative_layer() -> list[dict[str, Any]]:
    from src.v10_action_engine_organ import build_v10_action_engine_status
    from src.v10_core_organ import build_v10_core_status
    from src.v10_runtime_organ import build_v10_runtime_status

    return [
        _organ_posture_item("v10_core_organ", build_v10_core_status()),
        _organ_posture_item("v10_runtime_organ", build_v10_runtime_status()),
        _organ_posture_item(
            "v10_action_engine_organ", build_v10_action_engine_status()
        ),
    ]


def _build_naming_protocol_layer() -> list[dict[str, Any]]:
    from src.mythic_engineering_translator_organ import (
        build_mythic_engineering_translator_status,
    )
    from src.naming_genome_organ import build_naming_genome_status
    from src.naming_protocol_organ import build_naming_protocol_status

    return [
        _organ_posture_item("naming_protocol_organ", build_naming_protocol_status()),
        _organ_posture_item("naming_genome_organ", build_naming_genome_status()),
        _organ_posture_item(
            "mythic_engineering_translator_organ",
            build_mythic_engineering_translator_status(),
        ),
    ]


def _build_linguistic_mutation_layer() -> list[dict[str, Any]]:
    from src.linguistic_drift_predictor_organ import (
        build_linguistic_drift_predictor_status,
    )
    from src.linguistic_lineage_viz_organ import build_linguistic_lineage_viz_status
    from src.linguistic_mutation_organ import build_linguistic_mutation_status

    return [
        _organ_posture_item(
            "linguistic_mutation_organ", build_linguistic_mutation_status()
        ),
        _organ_posture_item(
            "linguistic_drift_predictor_organ",
            build_linguistic_drift_predictor_status(),
        ),
        _organ_posture_item(
            "linguistic_lineage_viz_organ", build_linguistic_lineage_viz_status()
        ),
    ]


def _build_meta_linguistic_orchestration_layer() -> list[dict[str, Any]]:
    from src.linguistic_cascade_organ import build_linguistic_cascade_status
    from src.linguistic_remediation_organ import build_linguistic_remediation_status
    from src.meta_linguistic_governance_organ import (
        build_meta_linguistic_governance_status,
    )

    return [
        _organ_posture_item(
            "linguistic_remediation_organ", build_linguistic_remediation_status()
        ),
        _organ_posture_item("linguistic_cascade_organ", build_linguistic_cascade_status()),
        _organ_posture_item(
            "meta_linguistic_governance_organ",
            build_meta_linguistic_governance_status(),
        ),
    ]


def _build_linguistic_forecast_layer() -> list[dict[str, Any]]:
    from src.linguistic_drift_forecast_organ import build_linguistic_drift_forecast_status
    from src.linguistic_forecast_consumption_organ import (
        build_linguistic_forecast_consumption_status,
    )
    from src.linguistic_preemptive_remediation_organ import (
        build_linguistic_preemptive_remediation_status,
    )

    return [
        _organ_posture_item(
            "linguistic_drift_forecast_organ",
            build_linguistic_drift_forecast_status(),
        ),
        _organ_posture_item(
            "linguistic_preemptive_remediation_organ",
            build_linguistic_preemptive_remediation_status(),
        ),
        _organ_posture_item(
            "linguistic_forecast_consumption_organ",
            build_linguistic_forecast_consumption_status(),
        ),
    ]


def _build_linguistic_predictive_cycle_layer() -> list[dict[str, Any]]:
    from src.linguistic_closed_loop_fabric_organ import (
        build_linguistic_closed_loop_fabric_status,
    )
    from src.linguistic_predictive_cycle_history_organ import (
        build_linguistic_predictive_cycle_history_status,
    )
    from src.linguistic_predictive_governance_organ import (
        build_linguistic_predictive_governance_status,
    )

    return [
        _organ_posture_item(
            "linguistic_predictive_governance_organ",
            build_linguistic_predictive_governance_status(),
        ),
        _organ_posture_item(
            "linguistic_predictive_cycle_history_organ",
            build_linguistic_predictive_cycle_history_status(),
        ),
        _organ_posture_item(
            "linguistic_closed_loop_fabric_organ",
            build_linguistic_closed_loop_fabric_status(),
        ),
    ]


def _build_linguistic_governance_cycle_layer() -> list[dict[str, Any]]:
    from src.linguistic_cycle_optimization_organ import (
        build_linguistic_cycle_optimization_status,
    )
    from src.linguistic_governance_cycle_history_organ import (
        build_linguistic_governance_cycle_history_status,
    )
    from src.linguistic_governance_cycle_organ import (
        build_linguistic_governance_cycle_status,
    )

    return [
        _organ_posture_item(
            "linguistic_governance_cycle_organ",
            build_linguistic_governance_cycle_status(),
        ),
        _organ_posture_item(
            "linguistic_governance_cycle_history_organ",
            build_linguistic_governance_cycle_history_status(),
        ),
        _organ_posture_item(
            "linguistic_cycle_optimization_organ",
            build_linguistic_cycle_optimization_status(),
        ),
    ]


def _safety_halt_from_status(safety_status: dict[str, Any]) -> bool:
    return bool((safety_status.get("thresholds") or {}).get("halt_required"))


def build_coherence_fabric_status(
    *,
    root: Path | None = None,
    bridge_snapshot: dict[str, Any] | None = None,
    pipeline_trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Join profile, lane, and envelope posture into one inspectable snapshot."""
    root = _root(root)
    profile = build_operator_profile()
    authority_lane = str(profile.get("authority_lane") or "operator")
    lane_report = load_awakened_lanes(root)
    resolution = resolve_lane_for_gene(
        "adaptive_lane_organ",
        root=root,
        authority_lane=authority_lane,
    )

    bridge_env = to_bridge_envelope(bridge_snapshot or _idle_bridge_snapshot())
    pipeline_source = pipeline_trace if isinstance(pipeline_trace, dict) and pipeline_trace else None
    pipeline_env = to_pipeline_envelope(
        pipeline_source or _idle_pipeline_baseline()
    )
    protocol = coherence_protocol_from_pipeline(pipeline_source)
    pipeline_governance_mode = "strict"
    if protocol["response"] == "BLOCK":
        pipeline_governance_mode = "halt"
    memory_env = to_memory_board_envelope(
        build_memory_board_snapshot(build_default_memory_controller())
    )
    safety_status = build_envelope_status(root=root)
    safety_mode = (
        "halt"
        if bool((safety_status.get("thresholds") or {}).get("halt_required"))
        else "strict"
    )

    envelope_governance_modes = [
        {
            "envelope_id": "capability_service_bridge",
            "governance_mode": str(bridge_env.get("governance_mode") or "strict"),
        },
        {
            "envelope_id": "governed_direct_pipeline",
            "governance_mode": pipeline_governance_mode,
        },
        {
            "envelope_id": "jarvis_memory_board",
            "governance_mode": "strict",
        },
        {
            "envelope_id": "safety_envelope",
            "governance_mode": safety_mode,
        },
    ]

    fabric_aligned = _fabric_genes_aligned(root)
    safety_halt = safety_mode == "halt"
    pipeline_allowed = evaluate_pipeline_coherence(
        fabric_genes_aligned=fabric_aligned,
        safety_halt=safety_halt,
    ).allowed
    if pipeline_source and protocol["response"] == "BLOCK":
        pipeline_allowed = False

    mind_posture = _build_mind_posture(pipeline_trace=pipeline_source)
    infrastructure_posture = _build_infrastructure_posture(pipeline_trace=pipeline_source)
    memory_posture = _build_memory_governance_posture()
    forensics_posture = _build_forensics_posture()
    immune_posture = _build_immune_observe_posture(pipeline_trace=pipeline_source)
    authority_trace_posture = _build_authority_trace_posture()
    mission_boundary_posture = _build_mission_boundary_posture()
    coding_posture = _build_coding_posture()
    otem_lane_posture = _build_otem_lane_posture()
    predictive_lane_posture = _build_predictive_lane_posture(pipeline_trace=pipeline_source)
    execution_depth_posture = _build_execution_depth_posture()
    constitutional_creative_posture = _build_constitutional_creative_posture()
    story_chain_posture = _build_story_chain_posture()
    module_governance_posture = _build_module_governance_posture()
    perception_posture = _build_perception_posture()
    spatial_symbolic_posture = _build_spatial_symbolic_posture()
    route_choice_posture = _build_route_choice_posture()
    executive_attention_posture = _build_executive_attention_posture()
    deliberation_planning_posture = _build_deliberation_planning_posture()
    voice_execution_posture = _build_voice_execution_posture()
    factory_fabrication_posture = _build_factory_fabrication_posture()
    contractor_lane_posture = _build_contractor_lane_posture()
    kinetic_shell_posture = _build_kinetic_shell_posture()
    protocol_posture = _build_protocol_posture()
    authority_shell_posture = _build_authority_shell_posture()
    response_integrity_posture = _build_response_integrity_posture()
    law_cycle_posture = _build_law_cycle_posture()
    turn_admission_posture = _build_turn_admission_posture()
    governance_control_posture = _build_governance_control_posture()
    product_shell_posture = _build_product_shell_posture()
    operator_surface_posture = _build_operator_surface_posture()
    composed_runtime_posture = _build_composed_runtime_posture()
    workspace_memory_layer = _build_workspace_memory_layer()
    hygiene_blueprint_layer = _build_hygiene_blueprint_layer()
    extended_operator_interface_layer = _build_extended_operator_interface_layer()
    creative_core_layer = _build_creative_core_layer()
    v9_creative_layer = _build_v9_creative_layer()
    v10_creative_layer = _build_v10_creative_layer()
    naming_protocol_layer = _build_naming_protocol_layer()
    linguistic_mutation_layer = _build_linguistic_mutation_layer()
    meta_linguistic_orchestration_layer = _build_meta_linguistic_orchestration_layer()
    linguistic_forecast_layer = _build_linguistic_forecast_layer()
    linguistic_predictive_cycle_layer = _build_linguistic_predictive_cycle_layer()
    linguistic_governance_cycle_layer = _build_linguistic_governance_cycle_layer()

    payload: dict[str, Any] = {
        "operator_cognition_coherence_fabric_version": COHERENCE_FABRIC_SCHEMA_VERSION,
        "authority_lane": authority_lane,
        "resolved_lane": str(resolution.lane_id or authority_lane),
        "envelope_governance_modes": envelope_governance_modes,
        "runtime_posture": _build_runtime_posture(),
        "mind_posture": mind_posture,
        "mind_planes_aligned": _mind_planes_aligned(mind_posture),
        "infrastructure_posture": infrastructure_posture,
        "infrastructure_substrate_aligned": _infrastructure_substrate_aligned(
            infrastructure_posture
        ),
        "memory_governance_posture": memory_posture,
        "memory_paths_aligned": _memory_paths_aligned(memory_posture),
        "forensics_posture": forensics_posture,
        "forensics_handoff_aligned": _forensics_handoff_aligned(forensics_posture),
        "immune_observe_posture": immune_posture,
        "immune_observe_aligned": _immune_observe_aligned(
            immune_posture,
            require_bridge=bool(pipeline_source),
        ),
        "authority_trace_posture": authority_trace_posture,
        "authority_trace_aligned": _authority_trace_aligned(authority_trace_posture),
        "mission_boundary_posture": mission_boundary_posture,
        "mission_boundary_aligned": _mission_boundary_aligned(mission_boundary_posture),
        "coding_posture": coding_posture,
        "coding_stack_aligned": _coding_stack_aligned(coding_posture),
        "otem_lane_posture": otem_lane_posture,
        "otem_lane_aligned": _otem_lane_aligned(otem_lane_posture),
        "predictive_lane_posture": predictive_lane_posture,
        "predictive_lane_aligned": _predictive_lane_aligned(predictive_lane_posture),
        "execution_depth_posture": execution_depth_posture,
        "execution_depth_aligned": _execution_depth_aligned(execution_depth_posture),
        "constitutional_creative_posture": constitutional_creative_posture,
        "constitutional_creative_aligned": _constitutional_creative_aligned(
            constitutional_creative_posture
        ),
        "story_chain_posture": story_chain_posture,
        "story_chain_aligned": _story_chain_aligned(story_chain_posture),
        "module_governance_posture": module_governance_posture,
        "module_governance_aligned": _module_governance_aligned(
            module_governance_posture
        ),
        "creative_chain_aligned": _story_chain_aligned(story_chain_posture)
        and _constitutional_creative_aligned(constitutional_creative_posture),
        "perception_posture": perception_posture,
        "perception_aligned": _perception_aligned(perception_posture),
        "spatial_symbolic_posture": spatial_symbolic_posture,
        "spatial_symbolic_aligned": _spatial_symbolic_aligned(spatial_symbolic_posture),
        "route_choice_posture": route_choice_posture,
        "route_choice_aligned": _route_choice_aligned(route_choice_posture),
        "executive_attention_posture": executive_attention_posture,
        "executive_attention_aligned": _executive_attention_aligned(
            executive_attention_posture
        ),
        "deliberation_planning_posture": deliberation_planning_posture,
        "deliberation_planning_aligned": _deliberation_planning_aligned(
            deliberation_planning_posture
        ),
        "voice_execution_posture": voice_execution_posture,
        "voice_execution_aligned": _voice_execution_aligned(voice_execution_posture),
        "nova_lobe_voice_aligned": (
            _executive_attention_aligned(executive_attention_posture)
            and _deliberation_planning_aligned(deliberation_planning_posture)
            and _voice_execution_aligned(voice_execution_posture)
        ),
        "factory_fabrication_posture": factory_fabrication_posture,
        "factory_fabrication_aligned": _factory_fabrication_aligned(
            factory_fabrication_posture
        ),
        "contractor_lane_posture": contractor_lane_posture,
        "contractor_lanes_aligned": _contractor_lanes_aligned(contractor_lane_posture),
        "kinetic_shell_posture": kinetic_shell_posture,
        "kinetic_shell_aligned": _kinetic_shell_aligned(kinetic_shell_posture),
        "factory_kinetic_aligned": (
            _factory_fabrication_aligned(factory_fabrication_posture)
            and _contractor_lanes_aligned(contractor_lane_posture)
            and _kinetic_shell_aligned(kinetic_shell_posture)
        ),
        "protocol_posture": protocol_posture,
        "protocol_aligned": _protocol_aligned(protocol_posture),
        "authority_shell_posture": authority_shell_posture,
        "authority_shell_aligned": _authority_shell_aligned(authority_shell_posture),
        "response_integrity_posture": response_integrity_posture,
        "response_integrity_aligned": _response_integrity_aligned(
            response_integrity_posture
        ),
        "authority_protocol_integrity_aligned": (
            _protocol_aligned(protocol_posture)
            and _authority_shell_aligned(authority_shell_posture)
            and _response_integrity_aligned(response_integrity_posture)
        ),
        "law_cycle_posture": law_cycle_posture,
        "law_cycle_aligned": _law_cycle_aligned(law_cycle_posture),
        "turn_admission_posture": turn_admission_posture,
        "turn_admission_aligned": _turn_admission_aligned(turn_admission_posture),
        "governance_control_posture": governance_control_posture,
        "governance_control_aligned": _governance_control_aligned(
            governance_control_posture
        ),
        "project_infi_law_aligned": (
            _law_cycle_aligned(law_cycle_posture)
            and _turn_admission_aligned(turn_admission_posture)
            and _governance_control_aligned(governance_control_posture)
        ),
        "product_shell_posture": product_shell_posture,
        "product_shell_aligned": _product_shell_aligned(product_shell_posture),
        "operator_surface_posture": operator_surface_posture,
        "operator_surface_aligned": _operator_surface_aligned(
            operator_surface_posture
        ),
        "composed_runtime_posture": composed_runtime_posture,
        "composed_runtime_aligned": _composed_runtime_aligned(
            composed_runtime_posture
        ),
        "operator_product_shell_aligned": (
            _product_shell_aligned(product_shell_posture)
            and _operator_surface_aligned(operator_surface_posture)
            and _composed_runtime_aligned(composed_runtime_posture)
        ),
        "workspace_memory_layer": workspace_memory_layer,
        "workspace_memory_aligned": _layer_aligned(
            workspace_memory_layer, minimum=3
        ),
        "hygiene_blueprint_layer": hygiene_blueprint_layer,
        "hygiene_blueprint_aligned": _layer_aligned(
            hygiene_blueprint_layer, minimum=3
        ),
        "extended_operator_interface_layer": extended_operator_interface_layer,
        "extended_operator_interface_aligned": _layer_aligned(
            extended_operator_interface_layer, minimum=3
        ),
        "operator_workspace_interfaces_aligned": (
            _layer_aligned(workspace_memory_layer, minimum=3)
            and _layer_aligned(hygiene_blueprint_layer, minimum=3)
            and _layer_aligned(extended_operator_interface_layer, minimum=3)
        ),
        "creative_core_layer": creative_core_layer,
        "creative_core_aligned": _layer_aligned(creative_core_layer, minimum=3),
        "v9_creative_layer": v9_creative_layer,
        "v9_creative_aligned": _layer_aligned(v9_creative_layer, minimum=3),
        "v10_creative_layer": v10_creative_layer,
        "v10_creative_aligned": _layer_aligned(v10_creative_layer, minimum=3),
        "creative_runtime_v9_v10_aligned": (
            _layer_aligned(creative_core_layer, minimum=3)
            and _layer_aligned(v9_creative_layer, minimum=3)
            and _layer_aligned(v10_creative_layer, minimum=3)
        ),
        "naming_protocol_layer": naming_protocol_layer,
        "naming_protocol_aligned": _layer_aligned(naming_protocol_layer, minimum=3),
        "linguistic_mutation_layer": linguistic_mutation_layer,
        "linguistic_mutation_aligned": _layer_aligned(
            linguistic_mutation_layer, minimum=3
        ),
        "meta_linguistic_orchestration_layer": meta_linguistic_orchestration_layer,
        "meta_linguistic_orchestration_aligned": _layer_aligned(
            meta_linguistic_orchestration_layer, minimum=3
        ),
        "meta_linguistic_governance_aligned": (
            _layer_aligned(naming_protocol_layer, minimum=3)
            and _layer_aligned(linguistic_mutation_layer, minimum=3)
            and _layer_aligned(meta_linguistic_orchestration_layer, minimum=3)
        ),
        "linguistic_forecast_layer": linguistic_forecast_layer,
        "linguistic_forecast_aligned": _layer_aligned(
            linguistic_forecast_layer, minimum=3
        ),
        "linguistic_predictive_cycle_layer": linguistic_predictive_cycle_layer,
        "linguistic_predictive_cycle_aligned": _layer_aligned(
            linguistic_predictive_cycle_layer, minimum=3
        ),
        "linguistic_governance_cycle_layer": linguistic_governance_cycle_layer,
        "linguistic_governance_cycle_aligned": _layer_aligned(
            linguistic_governance_cycle_layer, minimum=3
        ),
        "linguistic_closed_loop_aligned": (
            _layer_aligned(linguistic_forecast_layer, minimum=3)
            and _layer_aligned(linguistic_predictive_cycle_layer, minimum=3)
            and _layer_aligned(linguistic_governance_cycle_layer, minimum=3)
        ),
        "fabric_genes_aligned": fabric_aligned,
        "coherence_pipeline_allowed": pipeline_allowed,
        "safety_envelope_halt": safety_halt,
        "profile_posture": str(profile.get("claim_label") or "asserted"),
        "lane_awakened": bool(lane_report.get("awakened")),
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
    if pipeline_source:
        payload["last_coherence_response"] = protocol["response"]
        if protocol["reason"]:
            payload["last_coherence_reason"] = protocol["reason"]
    return payload


def _clip(value: Any, limit: int = MAX_FIELD_LEN) -> str:
    return str(value or "").strip()[:limit]


def build_governance_coherence_projection(
    status: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Bounded read-only governance posture for provider context (not Nova cortex)."""
    snapshot = status or build_coherence_fabric_status(root=root)
    modes = list(snapshot.get("envelope_governance_modes") or [])[:MAX_ENVELOPE_MODES]
    clipped_modes = [
        {
            "envelope_id": _clip(item.get("envelope_id"), 48),
            "governance_mode": _clip(item.get("governance_mode"), 24),
        }
        for item in modes
        if isinstance(item, dict)
    ]
    return {
        "projection_version": "1.0",
        "read_only": True,
        "source": "operator_cognition_coherence_fabric",
        "authority_lane": _clip(snapshot.get("authority_lane")),
        "resolved_lane": _clip(snapshot.get("resolved_lane")),
        "fabric_genes_aligned": bool(snapshot.get("fabric_genes_aligned")),
        "envelope_governance_modes": clipped_modes,
        "runtime_posture": list(snapshot.get("runtime_posture") or [])[:4],
        "mind_posture": list(snapshot.get("mind_posture") or [])[:4],
        "infrastructure_posture": list(snapshot.get("infrastructure_posture") or [])[:4],
        "infrastructure_substrate_aligned": bool(
            snapshot.get("infrastructure_substrate_aligned")
        ),
        "mind_planes_aligned": bool(snapshot.get("mind_planes_aligned")),
        "memory_governance_posture": list(snapshot.get("memory_governance_posture") or [])[:4],
        "memory_paths_aligned": bool(snapshot.get("memory_paths_aligned")),
        "forensics_posture": list(snapshot.get("forensics_posture") or [])[:4],
        "forensics_handoff_aligned": bool(snapshot.get("forensics_handoff_aligned")),
        "immune_observe_posture": list(snapshot.get("immune_observe_posture") or [])[:4],
        "immune_observe_aligned": bool(snapshot.get("immune_observe_aligned")),
        "authority_trace_posture": list(snapshot.get("authority_trace_posture") or [])[:4],
        "authority_trace_aligned": bool(snapshot.get("authority_trace_aligned")),
        "mission_boundary_posture": list(snapshot.get("mission_boundary_posture") or [])[:4],
        "mission_boundary_aligned": bool(snapshot.get("mission_boundary_aligned")),
        "coding_posture": list(snapshot.get("coding_posture") or [])[:4],
        "coding_stack_aligned": bool(snapshot.get("coding_stack_aligned")),
    }


def format_governance_coherence_block(projection: dict[str, Any] | None) -> str:
    """Format governance coherence for a system context module."""
    if not projection:
        return ""
    if not projection.get("fabric_genes_aligned"):
        return (
            "Governance coherence (read-only): fabric genes misaligned — "
            "bridge and pipeline policy paths may block until alignment is restored."
        )
    lines = [
        "Governance coherence (read-only; does not route or authorize):",
        f"- authority_lane: {projection.get('authority_lane')}",
        f"- resolved_lane: {projection.get('resolved_lane')}",
        f"- fabric_genes_aligned: {projection.get('fabric_genes_aligned')}",
    ]
    for item in projection.get("envelope_governance_modes") or []:
        if isinstance(item, dict):
            lines.append(
                f"- envelope {item.get('envelope_id')}: {item.get('governance_mode')}"
            )
    return "\n".join(lines)


def governance_coherence_projection_enabled() -> bool:
    """Env gate for OperatorGovernanceCoherenceModule (default on)."""
    raw = os.environ.get("AAIS_GOVERNANCE_COHERENCE_PROJECTION", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}
