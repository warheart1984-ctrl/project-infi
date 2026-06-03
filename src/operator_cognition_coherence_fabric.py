"""Operator Cognition Coherence Fabric — read-only cross-plane snapshot."""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COHERENCE_FABRIC_SCHEMA_VERSION = "operator_cognition_coherence_fabric.v1.8"
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
