"""Recipe Module Organ — read-only recipe workflow template posture."""

# Mythic: Recipe Module Organ
# Engineering: RecipeModuleEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-RMO-01"
ORGAN_VERSION = "recipe_module_organ.v1"


def build_recipe_module_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    module_present = (root / "src/recipe_module.py").is_file()
    genome_present = (root / "governance/subsystem_genomes/recipe_module.genome.v1.json").is_file()
    summary = f"module={int(module_present)};genome={int(genome_present)};operator_gated=1"[:128]
    return {
        "recipe_module_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "parent_genome_present": genome_present,
        "operator_gated": True,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
