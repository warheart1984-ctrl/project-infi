#!/usr/bin/env python3
"""Release 28 governed promotion eligibility."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT28_GENES = (
    "story_forge_launcher_organ",
    "movie_renderer_lane_organ",
    "text_game_to_video_organ",
    "game_front_door_organ",
    "text_to_3d_world_lane_organ",
    "world_pack_lane_organ",
)


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine
    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    GenomeEngine.reload(root)
    reg = GenomeEngine.registry()
    alt28_ready = sum(
        1
        for gene in ALT28_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    if alt28_ready != 6:
        errors.append(
            f"expected 6 Release 28 subsystems at mvp or governed (got {alt28_ready})"
        )

    for gene in ALT28_GENES:
        data = reg.genomes.get(gene)
        if not data:
            errors.append(f"missing genome: {gene}")
            continue
        stage = (data.get("identity") or {}).get("stage", "")
        if stage not in {"mvp", "governed"}:
            errors.append(f"{gene} must be mvp or governed (got {stage})")
        batch = (data.get("activation") or {}).get("batch_id", "")
        if batch != "alt28-summon-wave-2026-06":
            errors.append(f"{gene} activation.batch_id must be alt28 (got {batch})")

    fabric = build_coherence_fabric_status(root=root)
    version = fabric.get("operator_cognition_coherence_fabric_version")
    if version != "operator_cognition_coherence_fabric.v1.23":
        errors.append(f"coherence layer must be v1.23 (got {version})")
    if len(fabric.get("story_forge_expansion_layer") or []) < 6:
        errors.append("expected 6 story_forge_expansion_layer entries")
    if not fabric.get("story_forge_expansion_bundle_aligned"):
        errors.append("story_forge_expansion_bundle_aligned is false")

    closure = root / "docs/proof/storyforge/STORYFORGE_EXPANSION_BUNDLE_V1_PROOF.md"
    if not closure.is_file():
        errors.append("missing STORYFORGE_EXPANSION_BUNDLE_V1_PROOF.md")
    early = root / "docs/proof/platform/CISIV_EARLY_IDEAS_BUNDLE_V1_PROOF.md"
    if not early.is_file():
        errors.append("missing CISIV_EARLY_IDEAS_BUNDLE_V1_PROOF.md")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt28-governed-gate] FAIL: {err}")
        return 1
    print("[alt28-governed-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
