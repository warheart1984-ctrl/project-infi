"""Adaptive Lane Organ — wake Tier 5 operator-weighted lanes into live runtime."""

# Mythic: Adaptive Lane Organ
# Engineering: AdaptiveLaneInterface
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root, runtime_governance_dir
from src.governance_organs.genome_engine import GenomeEngine
from src.operator_profile_organ import build_operator_profile


@dataclass
class LaneResolution:
    lane_id: str
    weight: float
    capabilities: tuple[str, ...]
    gene: str | None = None
    allowed: bool = True
    reason: str | None = None


def _root(root: Path | None) -> Path:
    return root or repo_root()


def collect_operator_lanes(root: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """Return operator_lanes keyed by gene from the genome registry."""
    reg = GenomeEngine.reload(_root(root))
    by_gene: dict[str, list[dict[str, Any]]] = {}
    for gene, data in reg.genomes.items():
        lanes = (data.get("governance") or {}).get("operator_lanes") or []
        if lanes:
            by_gene[gene] = [dict(lane) for lane in lanes if isinstance(lane, dict)]
    return by_gene


def merge_lanes(
    by_gene: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Merge per-gene operator lanes into a weighted registry."""
    merged: dict[str, dict[str, Any]] = {}
    for gene, lanes in by_gene.items():
        for lane in lanes:
            lane_id = str(lane.get("lane_id") or "").strip()
            if not lane_id:
                continue
            entry = merged.setdefault(
                lane_id,
                {
                    "lane_id": lane_id,
                    "weight": 0.0,
                    "capabilities": set(),
                    "genes": [],
                },
            )
            entry["weight"] = max(entry["weight"], float(lane.get("weight") or 0.0))
            for cap in lane.get("capabilities") or []:
                entry["capabilities"].add(str(cap))
            if gene not in entry["genes"]:
                entry["genes"].append(gene)
    result = []
    for entry in merged.values():
        result.append(
            {
                "lane_id": entry["lane_id"],
                "weight": entry["weight"],
                "capabilities": sorted(entry["capabilities"]),
                "genes": list(entry["genes"]),
            }
        )
    result.sort(key=lambda item: (-item["weight"], item["lane_id"]))
    return result


def wake_adaptive_lanes(root: Path | None = None) -> dict[str, Any]:
    """Collect Tier 5 lanes, merge with operator authority, persist awakened snapshot."""
    root = _root(root)
    by_gene = collect_operator_lanes(root)
    lanes = merge_lanes(by_gene)
    profile = build_operator_profile()
    authority_lane = str(profile.get("authority_lane") or "operator")
    report: dict[str, Any] = {
        "adaptive_lane_organ_version": "adaptive_lane_organ.v1",
        "awakened": True,
        "authority_lane": authority_lane,
        "lane_count": len(lanes),
        "genes_with_lanes": sorted(by_gene.keys()),
        "lanes": lanes,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
    out = runtime_governance_dir() / "adaptive_lanes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def load_awakened_lanes(root: Path | None = None) -> dict[str, Any]:
    """Load persisted lane snapshot or wake lanes if missing."""
    path = runtime_governance_dir() / "adaptive_lanes.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return wake_adaptive_lanes(root)


def resolve_lane_for_gene(
    gene: str | None,
    *,
    root: Path | None = None,
    authority_lane: str | None = None,
) -> LaneResolution:
    """Resolve the highest-weight lane for a gene, defaulting to operator authority."""
    authority = str(authority_lane or build_operator_profile().get("authority_lane") or "operator")
    if not gene:
        return LaneResolution(lane_id=authority, weight=1.0, capabilities=())
    by_gene = collect_operator_lanes(root)
    lanes = by_gene.get(gene) or []
    if not lanes:
        return LaneResolution(lane_id=authority, weight=1.0, capabilities=(), gene=gene)
    best = max(lanes, key=lambda lane: float(lane.get("weight") or 0.0))
    lane_id = str(best.get("lane_id") or authority)
    caps = tuple(str(c) for c in (best.get("capabilities") or []))
    return LaneResolution(
        lane_id=lane_id,
        weight=float(best.get("weight") or 0.0),
        capabilities=caps,
        gene=gene,
        allowed=True,
    )


def lane_authorizes_capability(
    resolution: LaneResolution,
    capability_id: str | None,
    *,
    authority_lane: str | None = None,
) -> LaneResolution:
    """When a gene lane declares capabilities, require authority alignment for policy caps."""
    authority = str(authority_lane or build_operator_profile().get("authority_lane") or "operator")
    if not resolution.capabilities or not capability_id:
        return resolution
    cap = capability_id.replace("-", "_").strip().lower()
    policy_caps = {c.replace("-", "_").strip().lower() for c in resolution.capabilities}
    if cap not in policy_caps:
        return resolution
    if resolution.lane_id.replace("-", "_").strip().lower() != authority.replace("-", "_").strip().lower():
        return LaneResolution(
            lane_id=resolution.lane_id,
            weight=resolution.weight,
            capabilities=resolution.capabilities,
            gene=resolution.gene,
            allowed=False,
            reason=f"capability {capability_id} requires authority lane {authority}",
        )
    return resolution


def build_adaptive_lane_status(root: Path | None = None) -> dict[str, Any]:
    """Read-only status snapshot for the Alt-6 organ API."""
    return load_awakened_lanes(root)
