#!/usr/bin/env python3
"""Release 27 governed promotion eligibility."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT27_GENES = (
    "cisiv_operator_lineage_console",
    "forensic_triangulation",
    "capability_service_bridge",
    "jarvis_memory_board",
    "governed_direct_pipeline",
    "recipe_module",
    "imagine_generator",
    "narrative_trust_pack",
    "human_voice_extraction",
)

GOVERNED_PROOF_DIRS = {
    "cisiv_operator_lineage_console": "aais-ul",
    "forensic_triangulation": "forensics",
    "capability_service_bridge": "platform",
    "jarvis_memory_board": "platform",
    "governed_direct_pipeline": "platform",
    "recipe_module": "platform",
    "imagine_generator": "storyforge",
    "narrative_trust_pack": "storyforge",
    "human_voice_extraction": "speakers",
}


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine
    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    GenomeEngine.reload(root)
    reg = GenomeEngine.registry()
    alt27_ready = sum(
        1
        for gene in ALT27_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    if alt27_ready != 9:
        errors.append(
            f"expected 9 Release 27 subsystems at mvp or governed (got {alt27_ready})"
        )

    for gene in ALT27_GENES:
        data = reg.genomes.get(gene)
        if not data:
            errors.append(f"missing genome: {gene}")
            continue
        stage = (data.get("identity") or {}).get("stage", "")
        if stage not in {"mvp", "governed"}:
            errors.append(f"{gene} must be mvp or governed (got {stage})")
        batch = (data.get("activation") or {}).get("batch_id", "")
        if batch != "alt27-summon-wave-2026-06":
            errors.append(f"{gene} activation.batch_id must be alt27 (got {batch})")
        subdir = GOVERNED_PROOF_DIRS.get(gene, "platform")
        proof_path = root / f"docs/proof/{subdir}/{gene.upper()}_GOVERNED_PROOF.md"
        if not proof_path.is_file():
            errors.append(f"missing governed proof: {proof_path.relative_to(root)}")

    fabric = build_coherence_fabric_status(root=root)
    version = fabric.get("operator_cognition_coherence_fabric_version")
    if version != "operator_cognition_coherence_fabric.v1.22":
        errors.append(f"coherence layer must be v1.22 (got {version})")
    if len(fabric.get("cisiv_lineage_triangulation_layer") or []) < 2:
        errors.append("expected 2 cisiv_lineage_triangulation_layer entries")
    if len(fabric.get("constitutional_bridge_layer") or []) < 3:
        errors.append("expected 3 constitutional_bridge_layer entries")
    if len(fabric.get("creative_trust_chain_layer") or []) < 4:
        errors.append("expected 4 creative_trust_chain_layer entries")
    if not fabric.get("cisiv_early_ideas_bundle_aligned"):
        errors.append("cisiv_early_ideas_bundle_aligned is false")

    closure = root / "docs/proof/platform/CISIV_EARLY_IDEAS_BUNDLE_V1_PROOF.md"
    if not closure.is_file():
        errors.append("missing CISIV_EARLY_IDEAS_BUNDLE_V1_PROOF.md")
    op_closure = root / "docs/proof/platform/LINGUISTIC_OPERATIONAL_CLOSURE_V1_PROOF.md"
    if not op_closure.is_file():
        errors.append("missing LINGUISTIC_OPERATIONAL_CLOSURE_V1_PROOF.md")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt27-governed-gate] FAIL: {err}")
        return 1
    print("[alt27-governed-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
