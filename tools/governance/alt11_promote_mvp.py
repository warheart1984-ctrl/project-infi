#!/usr/bin/env python3
"""Promote Alt-11 concept genomes through prototype to MVP."""

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


ALT11_GENES = {
    "cognitive_bridge_organ": _entry("cognitive_bridge_organ", "cognitive-bridge", "cognitive-bridge-organ-gate"),
    "governed_event_chain_organ": _entry(
        "governed_event_chain_organ", "governed-event-chain", "governed-event-chain-organ-gate"
    ),
    "tracing_spine_organ": _entry("tracing_spine_organ", "tracing-spine", "tracing-spine-organ-gate"),
    "mission_board_organ": _entry("mission_board_organ", "mission-board", "mission-board-organ-gate"),
    "aris_boundary_organ": _entry("aris_boundary_organ", "aris-boundary", "aris-boundary-organ-gate"),
    "capability_module_organ": _entry(
        "capability_module_organ", "capability-module", "capability-module-organ-gate"
    ),
    "patchforge_organ": _entry("patchforge_organ", "patchforge", "patchforge-organ-gate"),
    "change_scope_organ": _entry("change_scope_organ", "change-scope", "change-scope-organ-gate"),
    "patch_verification_organ": _entry(
        "patch_verification_organ", "patch-verification", "patch-verification-organ-gate"
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
    for gene, spec in ALT11_GENES.items():
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt11] {gene} prototype blocked: {d1.failures}")
            return 1
        engine.apply(d1)
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt11] {gene} mvp blocked: {d2.failures}")
            return 1
        engine.apply(d2)
        print(f"[alt11] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
