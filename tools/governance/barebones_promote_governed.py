#!/usr/bin/env python3
"""Promote barebones summon wave genomes through prototype, MVP, and governed."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

MUTATION_CONTRACT = "docs/contracts/AAIS_SUBSYSTEM_MUTATION_PATH.md"
RETIREMENT_CONTRACT = "docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md"

BAREBONES_GENES = {
    "capability_service_bridge": {
        "active_doc": "docs/subsystems/platform/CAPABILITY_SERVICE_BRIDGE.md",
        "prototype_proof": "docs/proof/platform/CAPABILITY_SERVICE_BRIDGE_PROTOTYPE_PROOF.md",
        "v1_proof": "docs/proof/platform/CAPABILITY_SERVICE_BRIDGE_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/capability_service_bridge.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/capability_service_bridge.py"},
            {"kind": "api", "path": "GET /api/jarvis/capability-bridge"},
            {"kind": "api", "path": "GET /api/jarvis/capability-bridge/status"},
            {"kind": "gate", "path": "make capability-bridge-gate"},
        ],
    },
    "jarvis_memory_board": {
        "active_doc": "docs/subsystems/platform/JARVIS_MEMORY_BOARD.md",
        "prototype_proof": "docs/proof/platform/JARVIS_MEMORY_BOARD_PROTOTYPE_PROOF.md",
        "v1_proof": "docs/proof/platform/JARVIS_MEMORY_BOARD_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/jarvis_memory_board.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/jarvis_memory_board.py"},
            {"kind": "api", "path": "GET /api/jarvis/memory/board"},
            {"kind": "gate", "path": "make memory-board-gate"},
        ],
    },
    "governed_direct_pipeline": {
        "active_doc": "docs/runtime/GOVERNED_DIRECT_PIPELINE.md",
        "prototype_proof": "docs/proof/platform/GOVERNED_DIRECT_PIPELINE_PROTOTYPE_PROOF.md",
        "v1_proof": "docs/proof/platform/GOVERNED_DIRECT_PIPELINE_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/governed_direct_pipeline.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/governed_direct_pipeline.py"},
            {"kind": "api", "path": "GET /api/jarvis/pipeline/{turn_id}"},
            {"kind": "gate", "path": "make governed-pipeline-gate"},
        ],
    },
}


def _load(gene: str) -> dict:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _save(gene: str, data: dict) -> None:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _ensure_lifecycle_contracts(data: dict) -> None:
    gov = data.setdefault("governance", {})
    contracts = list(gov.get("contracts") or [])
    for path in (MUTATION_CONTRACT, RETIREMENT_CONTRACT):
        if path not in contracts:
            contracts.append(path)
    gov["contracts"] = contracts


def prepare_prototype(gene: str, spec: dict) -> None:
    data = _load(gene)
    _ensure_lifecycle_contracts(data)
    data.setdefault("runtime", {})["surface"] = spec["surface_prototype"]
    data.setdefault("proof", {})["bundles"] = [spec["prototype_proof"]]
    _save(gene, data)


def prepare_mvp(gene: str, spec: dict) -> None:
    data = _load(gene)
    _ensure_lifecycle_contracts(data)
    data.setdefault("runtime", {})["surface"] = spec["surface_mvp"]
    data.setdefault("proof", {})["bundles"] = [spec["v1_proof"]]
    data.setdefault("ssp", {})["active_doc"] = spec["active_doc"]
    data.setdefault("ssp", {})["summon_eligible"] = False
    _save(gene, data)


def promote_gene(engine: PromotionEngine, gene: str, spec: dict) -> int:
    prepare_prototype(gene, spec)
    decision = engine.evaluate(gene)
    if not decision.passed or decision.target_stage != "prototype":
        print(f"[barebones] {gene} prototype blocked: {decision.failures}")
        return 1
    decision = engine.apply(decision)
    if not decision.passed:
        print(f"[barebones] {gene} prototype apply failed: {decision.failures}")
        return 1
    print(f"[barebones] {gene} -> prototype")

    prepare_mvp(gene, spec)
    decision = engine.evaluate(gene)
    if not decision.passed or decision.target_stage != "mvp":
        print(f"[barebones] {gene} mvp blocked: {decision.failures}")
        return 1
    decision = engine.apply(decision)
    if not decision.passed:
        print(f"[barebones] {gene} mvp apply failed: {decision.failures}")
        return 1
    print(f"[barebones] {gene} -> mvp")

    decision = engine.evaluate(gene)
    if not decision.passed or decision.target_stage != "governed":
        print(f"[barebones] {gene} governed blocked: {decision.failures}")
        return 1
    decision = engine.apply(decision)
    if not decision.passed:
        print(f"[barebones] {gene} governed apply failed: {decision.failures}")
        return 1
    print(f"[barebones] {gene} -> governed")
    return 0


def main() -> int:
    engine = PromotionEngine(_ROOT)
    for gene, spec in BAREBONES_GENES.items():
        code = promote_gene(engine, gene, spec)
        if code != 0:
            return code
    print("[barebones] all genes promoted to governed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
