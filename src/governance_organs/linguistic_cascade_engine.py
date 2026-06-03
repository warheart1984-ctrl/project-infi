"""Linguistic cascade engine — Wave 10 lineage propagation policy."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from tools.linguistic_genome_lib import compute_fingerprints, load_genome, load_json


@dataclass
class CascadeChildImpact:
    gene: str
    drift_band: str
    drift_risk: int
    depth: int
    recommended_action: str = ""


@dataclass
class CascadeImpactReport:
    parent_gene: str
    parent_changed: bool
    children: list[CascadeChildImpact] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def load_cascade_policy(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    registry_path = root / "governance/meta_linguistic_registry.v1.json"
    policy_ref = "governance/linguistic_cascade_policy.v1.json"
    if registry_path.is_file():
        reg = load_json(registry_path)
        policy_ref = reg.get("cascade_policy_ref", policy_ref)
    path = root / policy_ref
    if not path.is_file():
        return {
            "version": "linguistic_cascade_policy.v1",
            "max_depth": 3,
            "block_apply_without_cascade_ack": False,
            "high_fanout_threshold": 4,
        }
    return load_json(path)


def affected_children(
    gene: str,
    root: Path | None = None,
    *,
    max_depth: int | None = None,
) -> list[tuple[str, int]]:
    root = root or repo_root()
    policy = load_cascade_policy(root)
    depth_limit = max_depth if max_depth is not None else int(policy.get("max_depth", 3))
    genome = load_genome(gene, root)
    if not genome:
        return []

    gdir = root / "governance/subsystem_genomes"
    all_genomes: dict[str, dict[str, Any]] = {}
    for path in gdir.glob("*.genome.v1.json"):
        data = load_json(path)
        g = (data.get("identity") or {}).get("gene")
        if g:
            all_genomes[g] = data

    result: list[tuple[str, int]] = []
    seen: set[str] = set()
    frontier: list[tuple[str, int]] = [(gene, 0)]
    while frontier:
        parent, depth = frontier.pop(0)
        if depth >= depth_limit:
            continue
        parent_data = all_genomes.get(parent)
        if not parent_data:
            continue
        for child in (parent_data.get("lineage") or {}).get("children") or []:
            if child in seen or child not in all_genomes:
                continue
            seen.add(child)
            child_depth = depth + 1
            result.append((child, child_depth))
            frontier.append((child, child_depth))
    return result


def cascade_impact(
    parent_gene: str,
    before_layers: dict[str, Any],
    after_layers: dict[str, Any],
    root: Path | None = None,
) -> CascadeImpactReport:
    root = root or repo_root()
    before_fp = compute_fingerprints(before_layers).get("combined", "")
    after_fp = compute_fingerprints(after_layers).get("combined", "")
    report = CascadeImpactReport(
        parent_gene=parent_gene,
        parent_changed=before_fp != after_fp,
    )
    if not report.parent_changed:
        return report

    from tools.linguistic_drift_predictor import score_gene

    for child, depth in affected_children(parent_gene, root):
        child_score = score_gene(child, root)
        action = "monitor"
        if child_score.band == "high":
            action = "review_mp_ling_or_wave2_header"
        elif child_score.band == "medium":
            action = "run_linguistic_diff"
        report.children.append(
            CascadeChildImpact(
                gene=child,
                drift_band=child_score.band,
                drift_risk=child_score.drift_risk,
                depth=depth,
                recommended_action=action,
            )
        )
    return report


def validate_cascade_ack(
    delta: dict[str, Any],
    root: Path | None = None,
) -> list[str]:
    root = root or repo_root()
    policy = load_cascade_policy(root)
    if not policy.get("block_apply_without_cascade_ack"):
        return []

    gene = delta.get("gene", "")
    before = delta.get("before") or {}
    after = delta.get("after") or {}
    layers_before = {"genome": before}
    layers_after = {"genome": after}
    impact = cascade_impact(gene, layers_before, layers_after, root)
    if not impact.parent_changed or not impact.children:
        return []

    ack = set(delta.get("cascade_ack") or [])
    required = {c.gene for c in impact.children if c.drift_band in {"medium", "high"}}
    missing = required - ack
    if missing:
        return [
            f"cascade_ack missing children: {sorted(missing)} "
            f"(policy block_apply_without_cascade_ack=true)"
        ]
    return []


def format_cascade_markdown(report: CascadeImpactReport) -> str:
    lines = [
        f"# Linguistic cascade report — `{report.parent_gene}`",
        "",
        f"Parent linguistic change: **{report.parent_changed}**",
        "",
    ]
    if not report.children:
        lines.append("_No downstream children within policy depth._")
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "| Child | Depth | Drift band | Risk | Recommended action |",
            "|-------|-------|------------|------|-------------------|",
        ]
    )
    for c in sorted(report.children, key=lambda x: (-x.drift_risk, x.gene)):
        lines.append(
            f"| `{c.gene}` | {c.depth} | {c.drift_band} | {c.drift_risk} | {c.recommended_action} |"
        )
    lines.append("")
    return "\n".join(lines)
