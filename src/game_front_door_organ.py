"""Game Front Door Organ — read-only /pipeline game front-door posture."""

# Mythic: Game Front Door Organ
# Engineering: GameFrontDoorPosture
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-GFD-01"
ORGAN_VERSION = "game_front_door_organ.v1"


def execute_game_front_door_admit(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    from src.capabilities.story_forge_organs import execute_game_front_door_admit as _run

    return _run(args, root=root)


def build_game_front_door_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = root / "external/story_forge/src/story_forge/engine.py"
    genome = root / "governance/subsystem_genomes/game_front_door_organ.genome.v1.json"
    proof = root / "docs/proof/storyforge/GAME_FRONT_DOOR_ORGAN_EXECUTION_V1_PROOF.md"
    present = engine.is_file()
    execution_ready = present and proof.is_file()
    summary = f"pipeline_game={int(execution_ready)};engine={int(present)};operator_gated=1"[:128]
    return {
        "game_front_door_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "engine_module_present": present,
        "parent_genome_present": genome.is_file(),
        "execution_path_ready": execution_ready,
        "front_door_active": execution_ready,
        "operator_gated": True,
        "bridge_safe": True,
        "proposal_only": not execution_ready,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
