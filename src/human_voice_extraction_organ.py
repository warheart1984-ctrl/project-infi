"""Human Voice Extraction Organ — read-only HVE retention and signoff posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-HVEO-01"
ORGAN_VERSION = "human_voice_extraction_organ.v1"


def build_human_voice_extraction_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    module_present = (root / "src/human_voice_extraction.py").is_file()
    genome_present = (
        root / "governance/subsystem_genomes/human_voice_extraction.genome.v1.json"
    ).is_file()
    summary = f"module={int(module_present)};retention_signoff=1;operator_gated=1"[:128]
    return {
        "human_voice_extraction_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "parent_genome_present": genome_present,
        "retention_signoff_required": True,
        "operator_gated": True,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
