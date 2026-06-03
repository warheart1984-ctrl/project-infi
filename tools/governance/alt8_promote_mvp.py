#!/usr/bin/env python3
"""Promote Alt-8 concept genomes through prototype to MVP."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

ALT8_GENES = {
    "continuity_witness_organ": {
        "active_doc": "docs/subsystems/nova/CONTINUITY_WITNESS_ORGAN.md",
        "prototype_proof": "docs/proof/cognitive_runtime/CONTINUITY_WITNESS_ORGAN_PROTOTYPE_PROOF.md",
        "v1_proof": "docs/proof/cognitive_runtime/CONTINUITY_WITNESS_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/continuity_witness_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/continuity_witness_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/continuity-witness/status"},
            {"kind": "gate", "path": "make continuity-witness-gate"},
        ],
    },
    "narrative_continuity_organ": {
        "active_doc": "docs/subsystems/nova/NARRATIVE_CONTINUITY_ORGAN.md",
        "prototype_proof": "docs/proof/cognitive_runtime/NARRATIVE_CONTINUITY_ORGAN_PROTOTYPE_PROOF.md",
        "v1_proof": "docs/proof/cognitive_runtime/NARRATIVE_CONTINUITY_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/narrative_continuity_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/narrative_continuity_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/narrative-continuity/status"},
            {"kind": "gate", "path": "make narrative-continuity-gate"},
        ],
    },
    "intent_agency_organ": {
        "active_doc": "docs/subsystems/nova/INTENT_AGENCY_ORGAN.md",
        "prototype_proof": "docs/proof/cognitive_runtime/INTENT_AGENCY_ORGAN_PROTOTYPE_PROOF.md",
        "v1_proof": "docs/proof/cognitive_runtime/INTENT_AGENCY_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/intent_agency_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/intent_agency_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/intent-agency/status"},
            {"kind": "gate", "path": "make intent-agency-gate"},
        ],
    },
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
    for gene, spec in ALT8_GENES.items():
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt8] {gene} prototype blocked: {d1.failures}")
            return 1
        engine.apply(d1)
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt8] {gene} mvp blocked: {d2.failures}")
            return 1
        engine.apply(d2)
        print(f"[alt8] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
