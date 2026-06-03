#!/usr/bin/env python3
"""Promote Release 22 concept schemas through prototype to MVP."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine


def _entry(gene: str, api: str, gate: str) -> dict:
    upper = gene.upper()
    return {
        "active_doc": f"docs/subsystems/platform/{upper}.md",
        "prototype_proof": f"docs/proof/platform/{upper}_V1_PROOF.md",
        "v1_proof": f"docs/proof/platform/{upper}_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": f"src/{gene}.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": f"src/{gene}.py"},
            {"kind": "api", "path": f"GET /api/jarvis/{api}/status"},
            {"kind": "gate", "path": f"make {gate}"},
        ],
    }


ALT22_GENES = {
    "naming_protocol_organ": _entry(
        "naming_protocol_organ", "naming-protocol", "naming-protocol-organ-gate"
    ),
    "naming_genome_organ": _entry(
        "naming_genome_organ", "naming-genome", "naming-genome-organ-gate"
    ),
    "linguistic_mutation_organ": _entry(
        "linguistic_mutation_organ",
        "linguistic-mutation",
        "linguistic-mutation-organ-gate",
    ),
    "mythic_engineering_translator_organ": _entry(
        "mythic_engineering_translator_organ",
        "mythic-engineering-translator",
        "mythic-engineering-translator-organ-gate",
    ),
    "linguistic_drift_predictor_organ": _entry(
        "linguistic_drift_predictor_organ",
        "linguistic-drift-predictor",
        "linguistic-drift-predictor-organ-gate",
    ),
    "linguistic_lineage_viz_organ": _entry(
        "linguistic_lineage_viz_organ",
        "linguistic-lineage-viz",
        "linguistic-lineage-viz-organ-gate",
    ),
    "linguistic_remediation_organ": _entry(
        "linguistic_remediation_organ",
        "linguistic-remediation",
        "linguistic-remediation-organ-gate",
    ),
    "linguistic_cascade_organ": _entry(
        "linguistic_cascade_organ", "linguistic-cascade", "linguistic-cascade-organ-gate"
    ),
    "meta_linguistic_governance_organ": _entry(
        "meta_linguistic_governance_organ",
        "meta-linguistic-governance",
        "meta-linguistic-governance-organ-gate",
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
    for gene, spec in ALT22_GENES.items():
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt22] {gene} prototype blocked: {d1.failures}")
            return 1
        d1_apply = engine.apply(d1)
        if not d1_apply.passed:
            print(f"[alt22] {gene} prototype apply failed: {d1_apply.failures}")
            return 1
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt22] {gene} mvp blocked: {d2.failures}")
            return 1
        engine.apply(d2)
        print(f"[alt22] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
