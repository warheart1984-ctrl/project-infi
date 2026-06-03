#!/usr/bin/env python3
"""Promote Alt-16 organs from MVP to governed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

ALT16_GOVERNED = {
    "ai_factory_organ": "docs/proof/ai_factory/AI_FACTORY_ORGAN_GOVERNED_PROOF.md",
    "cogos_runtime_bridge_organ": "docs/proof/platform/COGOS_RUNTIME_BRIDGE_ORGAN_GOVERNED_PROOF.md",
    "wolf_rehydration_organ": "docs/proof/platform/WOLF_REHYDRATION_ORGAN_GOVERNED_PROOF.md",
    "forge_contractor_organ": "docs/proof/platform/FORGE_CONTRACTOR_ORGAN_GOVERNED_PROOF.md",
    "forge_eval_organ": "docs/proof/platform/FORGE_EVAL_ORGAN_GOVERNED_PROOF.md",
    "evolve_engine_organ": "docs/proof/platform/EVOLVE_ENGINE_ORGAN_GOVERNED_PROOF.md",
    "slingshot_organ": "docs/proof/platform/SLINGSHOT_ORGAN_GOVERNED_PROOF.md",
    "operator_workbench_organ": "docs/proof/platform/OPERATOR_WORKBENCH_ORGAN_GOVERNED_PROOF.md",
    "workflow_shell_organ": "docs/proof/platform/WORKFLOW_SHELL_ORGAN_GOVERNED_PROOF.md",
}

ELIGIBILITY = _ROOT / "tools/governance/check_alt16_governed_eligibility.py"


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
        print("[alt16-governed] eligibility gate failed")
        return 1

    engine = PromotionEngine(_ROOT)
    for gene, proof in ALT16_GOVERNED.items():
        current = (_load(gene).get("identity") or {}).get("stage", "")
        if current == "governed":
            print(f"[alt16-governed] {gene} already governed")
            continue
        prepare_governed(gene, proof)
        decision = engine.evaluate(gene, run_gates=True)
        if not decision.passed or decision.target_stage != "governed":
            print(f"[alt16-governed] {gene} blocked: {decision.failures}")
            return 1
        decision = engine.apply(decision)
        if not decision.passed:
            print(f"[alt16-governed] {gene} apply failed: {decision.failures}")
            return 1
        print(f"[alt16-governed] {gene} -> governed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
