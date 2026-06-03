#!/usr/bin/env python3
"""Promote Alt-10 organs from MVP to governed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

ALT10_GOVERNED = {
    "verification_gate_organ": "docs/proof/platform/VERIFICATION_GATE_ORGAN_GOVERNED_PROOF.md",
    "memory_path_governance_organ": "docs/proof/platform/MEMORY_PATH_GOVERNANCE_ORGAN_GOVERNED_PROOF.md",
    "knowledge_authority_organ": "docs/proof/platform/KNOWLEDGE_AUTHORITY_ORGAN_GOVERNED_PROOF.md",
    "scorpion_bridge_organ": "docs/proof/forensics/SCORPION_BRIDGE_ORGAN_GOVERNED_PROOF.md",
    "mechanic_handoff_organ": "docs/proof/forensics/MECHANIC_HANDOFF_ORGAN_GOVERNED_PROOF.md",
    "forensic_triangulation_organ": "docs/proof/forensics/FORENSIC_TRIANGULATION_ORGAN_GOVERNED_PROOF.md",
    "immune_observe_organ": "docs/proof/nova/IMMUNE_OBSERVE_ORGAN_GOVERNED_PROOF.md",
    "policy_gate_organ": "docs/proof/nova/POLICY_GATE_ORGAN_GOVERNED_PROOF.md",
    "predictor_immune_bridge_organ": "docs/proof/nova/PREDICTOR_IMMUNE_BRIDGE_ORGAN_GOVERNED_PROOF.md",
}

ELIGIBILITY = _ROOT / "tools/governance/check_alt10_governed_eligibility.py"


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
        print("[alt10-governed] eligibility gate failed")
        return 1

    engine = PromotionEngine(_ROOT)
    for gene, proof in ALT10_GOVERNED.items():
        prepare_governed(gene, proof)
        decision = engine.evaluate(gene, run_gates=True)
        if not decision.passed or decision.target_stage != "governed":
            print(f"[alt10-governed] {gene} blocked: {decision.failures}")
            return 1
        decision = engine.apply(decision)
        if not decision.passed:
            print(f"[alt10-governed] {gene} apply failed: {decision.failures}")
            return 1
        print(f"[alt10-governed] {gene} -> governed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
