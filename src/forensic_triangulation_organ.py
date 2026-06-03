"""Forensic Triangulation Organ — read-only shell over triangulation correlator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-FT-01"
ORGAN_VERSION = "forensic_triangulation_organ.v1"


def build_forensic_triangulation_status(*, root: Path | None = None) -> dict[str, Any]:
    """Bounded triangulation organ posture; subordinate to forensic_triangulation genome."""
    root = root or Path(__file__).resolve().parents[1]
    tri_root = root / "triangulation"
    package_present = (tri_root / "__init__.py").is_file() or (tri_root / "correlate.py").is_file()
    genome_path = root / "governance/subsystem_genomes/forensic_triangulation.genome.v1.json"
    genome_stage = "unknown"
    if genome_path.is_file():
        genome = json.loads(genome_path.read_text(encoding="utf-8"))
        genome_stage = str((genome.get("identity") or {}).get("stage") or "unknown")
    fixture_cases = 0
    fixtures = tri_root / "fixtures"
    if fixtures.is_dir():
        fixture_cases = sum(1 for item in fixtures.iterdir() if item.is_dir())
    summary = (
        f"package={'ok' if package_present else 'missing'};"
        f"genome={genome_stage};fixtures={fixture_cases}"
    )[:128]
    return {
        "forensic_triangulation_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "triangulation_package_present": package_present,
        "parent_genome_stage": genome_stage,
        "fixture_case_count": fixture_cases,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
