#!/usr/bin/env python3
"""Promote Alt-18 concept genomes through prototype to MVP."""

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


ALT18_GENES = {
    "project_infi_state_machine_organ": _entry(
        "project_infi_state_machine_organ",
        "project-infi-state-machine",
        "project-infi-state-machine-organ-gate",
    ),
    "project_infi_law_organ": _entry(
        "project_infi_law_organ", "project-infi-law", "project-infi-law-organ-gate"
    ),
    "run_ledger_binding_organ": _entry(
        "run_ledger_binding_organ",
        "run-ledger-binding",
        "run-ledger-binding-organ-gate",
    ),
    "chat_turn_governance_organ": _entry(
        "chat_turn_governance_organ",
        "chat-turn-governance",
        "chat-turn-governance-organ-gate",
    ),
    "aais_ul_substrate_organ": _entry(
        "aais_ul_substrate_organ",
        "aais-ul-substrate",
        "aais-ul-substrate-organ-gate",
    ),
    "aris_integration_organ": _entry(
        "aris_integration_organ", "aris-integration", "aris-integration-organ-gate"
    ),
    "governance_layer_organ": _entry(
        "governance_layer_organ", "governance-layer", "governance-layer-organ-gate"
    ),
    "security_protocol_organ": _entry(
        "security_protocol_organ", "security-protocol", "security-protocol-organ-gate"
    ),
    "system_guard_organ": _entry(
        "system_guard_organ", "system-guard", "system-guard-organ-gate"
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
    for gene, spec in ALT18_GENES.items():
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt18] {gene} prototype blocked: {d1.failures}")
            return 1
        d1_apply = engine.apply(d1)
        if not d1_apply.passed:
            print(f"[alt18] {gene} prototype apply failed: {d1_apply.failures}")
            return 1
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt18] {gene} mvp blocked: {d2.failures}")
            return 1
        engine.apply(d2)
        print(f"[alt18] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
