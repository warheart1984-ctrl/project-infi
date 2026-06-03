"""Operator Cognition Coherence Fabric — read-only cross-plane snapshot."""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COHERENCE_FABRIC_SCHEMA_VERSION = "operator_cognition_coherence_fabric.v1.2"
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

    payload: dict[str, Any] = {
        "operator_cognition_coherence_fabric_version": COHERENCE_FABRIC_SCHEMA_VERSION,
        "authority_lane": authority_lane,
        "resolved_lane": str(resolution.lane_id or authority_lane),
        "envelope_governance_modes": envelope_governance_modes,
        "runtime_posture": _build_runtime_posture(),
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
