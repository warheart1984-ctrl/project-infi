#!/usr/bin/env python3
"""Promote Release 21 concept schemas through prototype to MVP."""

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


ALT21_GENES = {
    "creative_core_runtime_organ": _entry(
        "creative_core_runtime_organ",
        "creative-core-runtime",
        "creative-core-runtime-organ-gate",
    ),
    "v9_core_organ": _entry("v9_core_organ", "v9-core", "v9-core-organ-gate"),
    "v9_runtime_organ": _entry(
        "v9_runtime_organ", "v9-runtime", "v9-runtime-organ-gate"
    ),
    "v10_core_organ": _entry("v10_core_organ", "v10-core", "v10-core-organ-gate"),
    "v10_runtime_organ": _entry(
        "v10_runtime_organ", "v10-runtime", "v10-runtime-organ-gate"
    ),
    "v10_action_engine_organ": _entry(
        "v10_action_engine_organ",
        "v10-action-engine",
        "v10-action-engine-organ-gate",
    ),
    "creative_capability_bridge_organ": _entry(
        "creative_capability_bridge_organ",
        "creative-capability-bridge",
        "creative-capability-bridge-organ-gate",
    ),
    "creative_operator_handoff_organ": _entry(
        "creative_operator_handoff_organ",
        "creative-operator-handoff",
        "creative-operator-handoff-organ-gate",
    ),
    "creative_console_interface_organ": _entry(
        "creative_console_interface_organ",
        "creative-console-interface",
        "creative-console-interface-organ-gate",
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
    for gene, spec in ALT21_GENES.items():
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt21] {gene} prototype blocked: {d1.failures}")
            return 1
        d1_apply = engine.apply(d1)
        if not d1_apply.passed:
            print(f"[alt21] {gene} prototype apply failed: {d1_apply.failures}")
            return 1
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt21] {gene} mvp blocked: {d2.failures}")
            return 1
        engine.apply(d2)
        print(f"[alt21] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
