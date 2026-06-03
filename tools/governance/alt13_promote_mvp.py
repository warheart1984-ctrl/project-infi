#!/usr/bin/env python3
"""Promote Alt-13 concept genomes through prototype to MVP."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine


def _entry(gene: str, api: str, gate: str, subdir: str) -> dict:
    upper = gene.upper()
    return {
        "active_doc": f"docs/subsystems/{subdir}/{upper}.md",
        "prototype_proof": f"docs/proof/{subdir}/{upper}_V1_PROOF.md",
        "v1_proof": f"docs/proof/{subdir}/{upper}_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": f"src/{gene}.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": f"src/{gene}.py"},
            {"kind": "api", "path": f"GET /api/jarvis/{api}/status"},
            {"kind": "gate", "path": f"make {gate}"},
        ],
    }


ALT13_GENES = {
    "ul_lineage_console_organ": _entry(
        "ul_lineage_console_organ", "ul-lineage-console", "ul-lineage-console-organ-gate", "aais-ul"
    ),
    "module_governance_organ": _entry(
        "module_governance_organ", "module-governance", "module-governance-organ-gate", "platform"
    ),
    "recipe_module_organ": _entry(
        "recipe_module_organ", "recipe-module", "recipe-module-organ-gate", "platform"
    ),
    "imagine_generator_organ": _entry(
        "imagine_generator_organ", "imagine-generator", "imagine-generator-organ-gate", "storyforge"
    ),
    "story_forge_lane_organ": _entry(
        "story_forge_lane_organ", "story-forge-lane", "story-forge-lane-organ-gate", "storyforge"
    ),
    "beatbox_lane_organ": _entry(
        "beatbox_lane_organ", "beatbox-lane", "beatbox-lane-organ-gate", "storyforge"
    ),
    "speakers_lane_organ": _entry(
        "speakers_lane_organ", "speakers-lane", "speakers-lane-organ-gate", "speakers"
    ),
    "human_voice_extraction_organ": _entry(
        "human_voice_extraction_organ",
        "human-voice-extraction",
        "human-voice-extraction-organ-gate",
        "speakers",
    ),
    "narrative_trust_pack_organ": _entry(
        "narrative_trust_pack_organ",
        "narrative-trust-pack",
        "narrative-trust-pack-organ-gate",
        "storyforge",
    ),
}


def _load(gene: str) -> dict:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _save(gene: str, data: dict) -> None:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def prepare_prototype(gene: str, spec: dict) -> None:
    data = _load(gene)
    data.setdefault("runtime", {})["surface"] = spec["surface_prototype"]
    data.setdefault("proof", {})["bundles"] = [spec["prototype_proof"]]
    _save(gene, data)


def prepare_mvp(gene: str, spec: dict) -> None:
    data = _load(gene)
    data.setdefault("runtime", {})["surface"] = spec["surface_mvp"]
    data.setdefault("proof", {})["bundles"] = [spec["v1_proof"]]
    data.setdefault("ssp", {})["active_doc"] = spec["active_doc"]
    data.setdefault("ssp", {})["summon_eligible"] = False
    _save(gene, data)


def main() -> int:
    engine = PromotionEngine(_ROOT)
    for gene, spec in ALT13_GENES.items():
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt13] {gene} prototype blocked: {d1.failures}")
            return 1
        d1_apply = engine.apply(d1)
        if not d1_apply.passed:
            print(f"[alt13] {gene} prototype apply failed: {d1_apply.failures}")
            return 1
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt13] {gene} mvp blocked: {d2.failures}")
            return 1
        engine.apply(d2)
        print(f"[alt13] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
