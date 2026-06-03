"""Naming Genome Subsystem — genome/alias linguistic cross-check posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-NGN-01"
ORGAN_VERSION = "naming_genome_organ.v1"


def build_naming_genome_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    lib = (root / "tools" / "linguistic_genome_lib.py").is_file()
    check = (root / "tools" / "governance" / "check_naming_genome.py").is_file()
    aliases = (root / "governance" / "legacy_engineering_aliases.v1.json").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "naming-genome-gate:" in m_text
    return {
        "naming_genome_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"lib={int(lib)};check={int(check)};aliases={int(aliases)}"[:128],
        "linguistic_genome_lib_present": lib,
        "check_naming_genome_present": check,
        "legacy_aliases_present": aliases,
        "naming_genome_gate_in_makefile": gate,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
