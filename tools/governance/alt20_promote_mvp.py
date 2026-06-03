#!/usr/bin/env python3
"""Promote Release 20 concept schemas through prototype to MVP."""

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


ALT20_GENES = {
    "memory_smith_organ": _entry(
        "memory_smith_organ", "memory-smith", "memory-smith-organ-gate"
    ),
    "operator_workspace_organ": _entry(
        "operator_workspace_organ",
        "operator-workspace",
        "operator-workspace-organ-gate",
    ),
    "jarvis_runs_organ": _entry(
        "jarvis_runs_organ", "jarvis-runs", "jarvis-runs-organ-gate"
    ),
    "state_hygiene_organ": _entry(
        "state_hygiene_organ", "state-hygiene", "state-hygiene-organ-gate"
    ),
    "blueprint_posture_organ": _entry(
        "blueprint_posture_organ",
        "blueprint-posture",
        "blueprint-posture-organ-gate",
    ),
    "workflow_interfaces_organ": _entry(
        "workflow_interfaces_organ",
        "workflow-interfaces",
        "workflow-interfaces-organ-gate",
    ),
    "platform_console_interfaces_organ": _entry(
        "platform_console_interfaces_organ",
        "platform-console-interfaces",
        "platform-console-interfaces-organ-gate",
    ),
    "operator_console_interface_organ": _entry(
        "operator_console_interface_organ",
        "operator-console-interface",
        "operator-console-interface-organ-gate",
    ),
    "nova_workspace_interface_organ": _entry(
        "nova_workspace_interface_organ",
        "nova-workspace-interface",
        "nova-workspace-interface-organ-gate",
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
    for gene, spec in ALT20_GENES.items():
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt20] {gene} prototype blocked: {d1.failures}")
            return 1
        d1_apply = engine.apply(d1)
        if not d1_apply.passed:
            print(f"[alt20] {gene} prototype apply failed: {d1_apply.failures}")
            return 1
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt20] {gene} mvp blocked: {d2.failures}")
            return 1
        engine.apply(d2)
        print(f"[alt20] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
