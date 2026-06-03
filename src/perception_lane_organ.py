"""Perception Lane Organ — read-only spatial/mystic lane chain posture."""

# Mythic: Perception Lane Organ
# Engineering: PerceptionLaneInterface
from __future__ import annotations

from typing import Any

from src.mystic_engine_organ import build_mystic_engine_status
from src.spatial_reasoning_organ import build_spatial_reasoning_status

MODULE_ID = "AAIS-PLO-01"
ORGAN_VERSION = "perception_lane_organ.v1"


def build_perception_lane_status() -> dict[str, Any]:
    spatial = build_spatial_reasoning_status()
    mystic = build_mystic_engine_status()
    chain = ["spatial_reasoning_organ", "mystic_engine_organ"]
    aligned = bool(
        spatial.get("bridge_safe")
        and mystic.get("bridge_safe")
        and spatial.get("operator_gated")
        and mystic.get("operator_gated")
    )
    summary = f"chain={len(chain)};aligned={int(aligned)};read_only=1"[:128]
    return {
        "perception_lane_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "lane_chain": chain,
        "spatial_bridge_capability": spatial.get("bridge_capability_id"),
        "mystic_bridge_capability": mystic.get("bridge_capability_id"),
        "lane_aligned": aligned,
        "bridge_safe": True,
        "operator_gated": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
