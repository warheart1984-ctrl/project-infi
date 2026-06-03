"""Movie Renderer Lane Organ — read-only movie renderer direct operator lane posture."""

# Mythic: Movie Renderer Lane Organ
# Engineering: MovieRendererLanePosture
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-MRL-01"
ORGAN_VERSION = "movie_renderer_lane_organ.v1"


def execute_movie_renderer_lane_render(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    from src.capabilities.story_forge_organs import execute_movie_renderer_lane_render as _run

    return _run(args, root=root)


def build_movie_renderer_lane_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    renderer = root / "external/story_forge/src/story_forge/movie_renderer.py"
    genome = root / "governance/subsystem_genomes/movie_renderer_lane_organ.genome.v1.json"
    proof = root / "docs/proof/storyforge/MOVIE_RENDERER_LANE_ORGAN_EXECUTION_V1_PROOF.md"
    present = renderer.is_file()
    execution_ready = present and proof.is_file()
    summary = f"movie_renderer={int(present)};exec={int(execution_ready)};operator_gated=1"[:128]
    return {
        "movie_renderer_lane_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "renderer_module_present": present,
        "parent_genome_present": genome.is_file(),
        "execution_path_ready": execution_ready,
        "direct_lane_active": execution_ready,
        "operator_gated": True,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
