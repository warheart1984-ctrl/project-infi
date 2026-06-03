#!/usr/bin/env python3
"""Promote Alt-10 concept genomes through prototype to MVP."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

def _entry(gene: str, subdir: str, api: str, gate: str) -> dict:
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


ALT10_GENES = {
    "verification_gate_organ": _entry(
        "verification_gate_organ", "platform", "verification-gate", "verification-gate-organ-gate"
    ),
    "memory_path_governance_organ": _entry(
        "memory_path_governance_organ",
        "platform",
        "memory-path-governance",
        "memory-path-governance-organ-gate",
    ),
    "knowledge_authority_organ": _entry(
        "knowledge_authority_organ",
        "platform",
        "knowledge-authority",
        "knowledge-authority-organ-gate",
    ),
    "scorpion_bridge_organ": _entry(
        "scorpion_bridge_organ", "forensics", "scorpion-bridge", "scorpion-bridge-organ-gate"
    ),
    "mechanic_handoff_organ": _entry(
        "mechanic_handoff_organ", "forensics", "mechanic-handoff", "mechanic-handoff-organ-gate"
    ),
    "forensic_triangulation_organ": _entry(
        "forensic_triangulation_organ",
        "forensics",
        "forensic-triangulation",
        "forensic-triangulation-organ-gate",
    ),
    "immune_observe_organ": _entry(
        "immune_observe_organ", "nova", "immune-observe", "immune-observe-organ-gate"
    ),
    "policy_gate_organ": _entry(
        "policy_gate_organ", "nova", "policy-gate", "policy-gate-organ-gate"
    ),
    "predictor_immune_bridge_organ": _entry(
        "predictor_immune_bridge_organ",
        "nova",
        "predictor-immune-bridge",
        "predictor-immune-bridge-organ-gate",
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
    for gene, spec in ALT10_GENES.items():
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt10] {gene} prototype blocked: {d1.failures}")
            return 1
        engine.apply(d1)
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt10] {gene} mvp blocked: {d2.failures}")
            return 1
        engine.apply(d2)
        print(f"[alt10] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
