#!/usr/bin/env python3
"""Alt-13 governed promotion eligibility — nine organs at MVP."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT13_GENES = (
    "ul_lineage_console_organ",
    "module_governance_organ",
    "recipe_module_organ",
    "imagine_generator_organ",
    "story_forge_lane_organ",
    "beatbox_lane_organ",
    "speakers_lane_organ",
    "human_voice_extraction_organ",
    "narrative_trust_pack_organ",
)

GOVERNED_PROOFS = {
    "ul_lineage_console_organ": _ROOT
    / "docs/proof/aais-ul/UL_LINEAGE_CONSOLE_ORGAN_GOVERNED_PROOF.md",
    "module_governance_organ": _ROOT
    / "docs/proof/platform/MODULE_GOVERNANCE_ORGAN_GOVERNED_PROOF.md",
    "recipe_module_organ": _ROOT / "docs/proof/platform/RECIPE_MODULE_ORGAN_GOVERNED_PROOF.md",
    "imagine_generator_organ": _ROOT
    / "docs/proof/storyforge/IMAGINE_GENERATOR_ORGAN_GOVERNED_PROOF.md",
    "story_forge_lane_organ": _ROOT
    / "docs/proof/storyforge/STORY_FORGE_LANE_ORGAN_GOVERNED_PROOF.md",
    "beatbox_lane_organ": _ROOT / "docs/proof/storyforge/BEATBOX_LANE_ORGAN_GOVERNED_PROOF.md",
    "speakers_lane_organ": _ROOT / "docs/proof/speakers/SPEAKERS_LANE_ORGAN_GOVERNED_PROOF.md",
    "human_voice_extraction_organ": _ROOT
    / "docs/proof/speakers/HUMAN_VOICE_EXTRACTION_ORGAN_GOVERNED_PROOF.md",
    "narrative_trust_pack_organ": _ROOT
    / "docs/proof/storyforge/NARRATIVE_TRUST_PACK_ORGAN_GOVERNED_PROOF.md",
}


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine
    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    GenomeEngine.reload(root)
    for gene in ALT13_GENES:
        data = GenomeEngine.registry().genomes.get(gene)
        if not data:
            errors.append(f"missing genome: {gene}")
            continue
        stage = (data.get("identity") or {}).get("stage", "")
        if stage not in {"mvp", "governed"}:
            errors.append(f"{gene} must be mvp before governed (got {stage})")
        surface = (data.get("runtime") or {}).get("surface") or []
        if not surface:
            errors.append(f"{gene} missing runtime.surface")
        proof_path = GOVERNED_PROOFS.get(gene)
        if proof_path and not proof_path.is_file():
            errors.append(f"missing governed proof: {proof_path.relative_to(root)}")

    fabric = build_coherence_fabric_status(root=root)
    if fabric.get("operator_cognition_coherence_fabric_version") != (
        "operator_cognition_coherence_fabric.v1.8"
    ):
        errors.append("coherence fabric must be v1.8")
    if len(fabric.get("constitutional_creative_posture") or []) != 5:
        errors.append("expected 5 constitutional_creative_posture entries")
    if len(fabric.get("story_chain_posture") or []) != 3:
        errors.append("expected 3 story_chain_posture entries")
    if len(fabric.get("module_governance_posture") or []) != 1:
        errors.append("expected 1 module_governance_posture entry")

    fabric_live = build_coherence_fabric_status(root=root)
    if not fabric_live.get("constitutional_creative_aligned"):
        errors.append("constitutional_creative_aligned is false")
    if not fabric_live.get("story_chain_aligned"):
        errors.append("story_chain_aligned is false")
    if not fabric_live.get("module_governance_aligned"):
        errors.append("module_governance_aligned is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt13-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT13_GENES],
            "tests/test_operator_cognition_coherence_fabric.py",
            "-q",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        print("[alt13-governed-gate] FAIL: organ pytest")
        return 1
    print("[alt13-governed-gate] PASS: Alt-13 organs eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
