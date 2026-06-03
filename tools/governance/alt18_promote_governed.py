#!/usr/bin/env python3
"""Promote Alt-18 organs from MVP to governed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

ALT18_GENES = (
    "project_infi_state_machine_organ",
    "project_infi_law_organ",
    "run_ledger_binding_organ",
    "chat_turn_governance_organ",
    "aais_ul_substrate_organ",
    "aris_integration_organ",
    "governance_layer_organ",
    "security_protocol_organ",
    "system_guard_organ",
)

GOVERNED_PROOFS = {
    gene: str(_ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md")
    for gene in ALT18_GENES
}

ELIGIBILITY = _ROOT / "tools/governance/check_alt18_governed_eligibility.py"


def _load(gene: str) -> dict:
    return json.loads(
        (_ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json").read_text(
            encoding="utf-8"
        )
    )


def _save(gene: str, data: dict) -> None:
    (_ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )


def prepare_governed(gene: str, proof: str) -> None:
    data = _load(gene)
    data.setdefault("proof", {})["bundles"] = [proof]
    _save(gene, data)


def main() -> int:
    proc = subprocess.run([sys.executable, str(ELIGIBILITY)], cwd=_ROOT, check=False)
    if proc.returncode != 0:
        return 1
    engine = PromotionEngine(_ROOT)
    for gene in ALT18_GENES:
        if (_load(gene).get("identity") or {}).get("stage") == "governed":
            print(f"[alt18-governed] {gene} already governed")
            continue
        prepare_governed(gene, GOVERNED_PROOFS[gene])
        decision = engine.evaluate(gene, run_gates=True)
        if not decision.passed or decision.target_stage != "governed":
            print(f"[alt18-governed] {gene} blocked: {decision.failures}")
            return 1
        decision = engine.apply(decision)
        if not decision.passed:
            return 1
        print(f"[alt18-governed] {gene} -> governed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
