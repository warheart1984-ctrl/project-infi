#!/usr/bin/env python3
"""Release 30 governed eligibility — 178 governed, coherence v1.24."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

BATCH = "alt30-summon-wave-2026-06"

RELEASE_30_GENES = (
    "coding_organs_stack",
    "otem_execution_substrate",
    "aris_standalone_service",
    "dreamspace_organ",
    "media_processor_family",
)

GOVERNED_GENOME_COUNT = 178


def check_genome_eligibility(root: Path | None = None) -> list[str]:
    """Genome posture only — safe to call from coherence fabric (no fabric snapshot)."""
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine

    GenomeEngine.reload(root)
    reg = GenomeEngine.registry()
    governed = sum(
        1
        for data in reg.genomes.values()
        if (data.get("identity") or {}).get("stage") == "governed"
    )
    if governed != GOVERNED_GENOME_COUNT:
        errors.append(f"expected {GOVERNED_GENOME_COUNT} governed genomes (got {governed})")

    otem_gate = root / "Makefile"
    if otem_gate.is_file():
        makefile_text = otem_gate.read_text(encoding="utf-8", errors="replace")
        if "otem-execution-substrate-gate:" not in makefile_text:
            errors.append("Makefile must define otem-execution-substrate-gate")
    else:
        errors.append("missing Makefile for otem-execution-substrate-gate")

    for gene in RELEASE_30_GENES:
        genome = reg.genomes.get(gene)
        if not genome:
            errors.append(f"missing genome: {gene}")
            continue
        if (genome.get("identity") or {}).get("stage") != "governed":
            errors.append(f"{gene} must be governed")
            continue
        batch_id = (genome.get("activation") or {}).get("batch_id")
        if batch_id != BATCH:
            errors.append(f"{gene} batch_id must be {BATCH} (got {batch_id})")

    return errors


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = list(check_genome_eligibility(root))

    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    fabric = build_coherence_fabric_status(root=root, skip_fabric_genes_alignment=True)
    version = fabric.get("operator_cognition_coherence_fabric_version")
    if version != "operator_cognition_coherence_fabric.v1.24":
        errors.append(f"coherence layer must be v1.24 (got {version})")
    if len(fabric.get("story_forge_execution_layer") or []) < 6:
        errors.append("expected 6 story_forge_execution_layer entries")
    if not fabric.get("story_forge_execution_bundle_aligned"):
        errors.append("story_forge_execution_bundle_aligned is false")
    if not fabric.get("integration_universal_bundle_aligned"):
        errors.append("integration_universal_bundle_aligned is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt30-governed-gate] FAIL: {err}")
        return 1
    print("[alt30-governed-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
