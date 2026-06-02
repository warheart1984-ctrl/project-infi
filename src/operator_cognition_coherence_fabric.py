"""Operator Cognition Coherence Fabric — read-only cross-plane snapshot."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


def build_coherence_fabric_status(
    *,
    root: Path | None = None,
    bridge_snapshot: dict[str, Any] | None = None,
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
    pipeline_env = to_pipeline_envelope(_idle_pipeline_baseline())
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
            "governance_mode": "strict",
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

    return {
        "operator_cognition_coherence_fabric_version": "operator_cognition_coherence_fabric.v1",
        "authority_lane": authority_lane,
        "resolved_lane": str(resolution.lane_id or authority_lane),
        "envelope_governance_modes": envelope_governance_modes,
        "fabric_genes_aligned": _fabric_genes_aligned(root),
        "profile_posture": str(profile.get("claim_label") or "asserted"),
        "lane_awakened": bool(lane_report.get("awakened")),
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
