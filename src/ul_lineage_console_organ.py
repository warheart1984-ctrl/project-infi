"""UL Lineage Console Organ — read-only CISIV operator lineage posture."""

# Mythic: Ul Lineage Console Organ
# Engineering: UlLineageConsoleInterface
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-ULC-01"
ORGAN_VERSION = "ul_lineage_console_organ.v1"


def build_ul_lineage_console_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    lineage_doc = root / "docs/runtime/UL_LINEAGE_CONSOLE.md"
    genome_present = (root / "governance/subsystem_genomes/cisiv_operator_lineage_console.genome.v1.json").is_file()
    summary = f"lineage_doc={int(lineage_doc.is_file())};genome={int(genome_present)};read_only=1"[:128]
    return {
        "ul_lineage_console_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "lineage_doc_present": lineage_doc.is_file(),
        "parent_genome_present": genome_present,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
