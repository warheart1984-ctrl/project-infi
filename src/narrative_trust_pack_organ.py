"""Narrative Trust Pack Organ — read-only NTP pack/verify/signoff posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-NTPO-01"
ORGAN_VERSION = "narrative_trust_pack_organ.v1"


def build_narrative_trust_pack_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    capability_present = (root / "src/capabilities/narrative_trust_pack.py").is_file()
    genome_present = (
        root / "governance/subsystem_genomes/narrative_trust_pack.genome.v1.json"
    ).is_file()
    summary = "ntp=pack_verify_signoff;auto_publish=0;signoff_required=1"[:128]
    return {
        "narrative_trust_pack_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "capability_present": capability_present,
        "parent_genome_present": genome_present,
        "auto_publish_allowed": False,
        "signoff_required": True,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
