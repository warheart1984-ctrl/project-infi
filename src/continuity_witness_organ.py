"""Continuity Witness Organ — read-only AAIS-CW-01 snapshot."""

# Mythic: Continuity Witness Organ
# Engineering: ContinuityWitnessEngine
from __future__ import annotations

from typing import Any

from src.continuity_witness import MODULE_ID, continuity_witness_store


def _drift_band_from_trajectory(trajectory_status: str) -> str:
    mapping = {
        "STABLE": "nominal",
        "WATCH": "watch",
        "DRIFTING": "drifting",
        "CRITICAL": "critical",
    }
    return mapping.get(str(trajectory_status or "").strip().upper(), "idle")


def build_continuity_witness_status(
    *,
    governed_pipeline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bounded witness snapshot for governance and coherence fabric join."""
    observation = continuity_witness_store.observe(governed_pipeline=governed_pipeline)
    trajectory = str(observation.get("trajectory_status") or "STABLE")
    coherence_protocol = dict((governed_pipeline or {}).get("coherence_protocol") or {})
    coherence_response = str(
        coherence_protocol.get("response")
        or observation.get("coherence_protocol_response")
        or "allow"
    ).strip().lower()
    coherence_boundary = coherence_response not in {"", "allow"}
    subsystems = dict(continuity_witness_store.snapshot().get("subsystems") or {})
    observation_count = sum(
        int((state or {}).get("turn_count") or 0) for state in subsystems.values()
    )
    return {
        "continuity_witness_organ_version": "continuity_witness_organ.v1",
        "module_id": MODULE_ID,
        "drift_band": _drift_band_from_trajectory(trajectory),
        "trajectory_status": trajectory[:32],
        "risk_level": str(observation.get("risk_level") or "low")[:32],
        "coherence_boundary": coherence_boundary,
        "coherence_protocol_response": coherence_response[:32],
        "observation_count": observation_count,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
