"""World Pack Lane Organ — read-only world pack registry lane posture."""

# Mythic: World Pack Lane Organ
# Engineering: WorldPackLanePosture
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-WPL-01"
ORGAN_VERSION = "world_pack_lane_organ.v1"


def build_world_pack_lane_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    worldpacks = root / "external/story_forge/src/story_forge/worldpacks"
    genome = root / "governance/subsystem_genomes/world_pack_lane_organ.genome.v1.json"
    present = worldpacks.is_dir()
    summary = f"worldpacks={int(present)};registry=0;operator_gated=1"[:128]
    return {
        "world_pack_lane_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "worldpacks_dir_present": present,
        "parent_genome_present": genome.is_file(),
        "registry_lane_active": False,
        "operator_gated": True,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
