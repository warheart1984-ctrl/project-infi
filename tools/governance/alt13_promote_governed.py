#!/usr/bin/env python3
"""Promote Alt-13 organs from MVP to governed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

ALT13_GOVERNED = {
    "ul_lineage_console_organ": "docs/proof/aais-ul/UL_LINEAGE_CONSOLE_ORGAN_GOVERNED_PROOF.md",
    "module_governance_organ": "docs/proof/platform/MODULE_GOVERNANCE_ORGAN_GOVERNED_PROOF.md",
    "recipe_module_organ": "docs/proof/platform/RECIPE_MODULE_ORGAN_GOVERNED_PROOF.md",
    "imagine_generator_organ": "docs/proof/storyforge/IMAGINE_GENERATOR_ORGAN_GOVERNED_PROOF.md",
    "story_forge_lane_organ": "docs/proof/storyforge/STORY_FORGE_LANE_ORGAN_GOVERNED_PROOF.md",
    "beatbox_lane_organ": "docs/proof/storyforge/BEATBOX_LANE_ORGAN_GOVERNED_PROOF.md",
    "speakers_lane_organ": "docs/proof/speakers/SPEAKERS_LANE_ORGAN_GOVERNED_PROOF.md",
    "human_voice_extraction_organ": "docs/proof/speakers/HUMAN_VOICE_EXTRACTION_ORGAN_GOVERNED_PROOF.md",
    "narrative_trust_pack_organ": "docs/proof/storyforge/NARRATIVE_TRUST_PACK_ORGAN_GOVERNED_PROOF.md",
}

ELIGIBILITY = _ROOT / "tools/governance/check_alt13_governed_eligibility.py"


def _load(gene: str) -> dict:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _save(gene: str, data: dict) -> None:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def prepare_governed(gene: str, proof: str) -> None:
    data = _load(gene)
    data.setdefault("proof", {})["bundles"] = [proof]
    _save(gene, data)


def main() -> int:
    proc = subprocess.run([sys.executable, str(ELIGIBILITY)], cwd=_ROOT, check=False)
    if proc.returncode != 0:
        print("[alt13-governed] eligibility gate failed")
        return 1

    engine = PromotionEngine(_ROOT)
    for gene, proof in ALT13_GOVERNED.items():
        prepare_governed(gene, proof)
        decision = engine.evaluate(gene, run_gates=True)
        if not decision.passed or decision.target_stage != "governed":
            print(f"[alt13-governed] {gene} blocked: {decision.failures}")
            return 1
        decision = engine.apply(decision)
        if not decision.passed:
            print(f"[alt13-governed] {gene} apply failed: {decision.failures}")
            return 1
        print(f"[alt13-governed] {gene} -> governed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
