"""World Pack Lane Organ — read-only world pack registry lane posture."""

# Mythic: World Pack Lane Organ
# Engineering: WorldPackLanePosture
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-WPL-01"
ORGAN_VERSION = "world_pack_lane_organ.v1"


def execute_world_pack_lane_inspect(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    from src.capabilities.story_forge_organs import execute_world_pack_lane_inspect as _run

    return _run(args, root=root)


def build_world_pack_lane_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    worldpacks = root / "external/story_forge/src/story_forge/worldpacks"
    genome = root / "governance/subsystem_genomes/world_pack_lane_organ.genome.v1.json"
    proof = root / "docs/proof/storyforge/WORLD_PACK_LANE_ORGAN_EXECUTION_V1_PROOF.md"
    present = worldpacks.is_dir()
    execution_ready = present and proof.is_file()
    summary = f"worldpacks={int(present)};exec={int(execution_ready)};operator_gated=1"[:128]
    return {
        "world_pack_lane_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "worldpacks_dir_present": present,
        "parent_genome_present": genome.is_file(),
        "execution_path_ready": execution_ready,
        "registry_lane_active": execution_ready,
        "operator_gated": True,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
