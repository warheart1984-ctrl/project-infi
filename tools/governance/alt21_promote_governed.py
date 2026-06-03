#!/usr/bin/env python3
"""Promote Release 21 subsystems from MVP to governed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

ALT21_GENES = (
    "creative_core_runtime_organ",
    "v9_core_organ",
    "v9_runtime_organ",
    "v10_core_organ",
    "v10_runtime_organ",
    "v10_action_engine_organ",
    "creative_capability_bridge_organ",
    "creative_operator_handoff_organ",
    "creative_console_interface_organ",
)

GOVERNED_PROOFS = {
    gene: str(_ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md")
    for gene in ALT21_GENES
}

ELIGIBILITY = _ROOT / "tools/governance/check_alt21_governed_eligibility.py"


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
    for gene in ALT21_GENES:
        if (_load(gene).get("identity") or {}).get("stage") == "governed":
            print(f"[alt21-governed] {gene} already governed")
            continue
        prepare_governed(gene, GOVERNED_PROOFS[gene])
        decision = engine.evaluate(gene, run_gates=True)
        if not decision.passed or decision.target_stage != "governed":
            print(f"[alt21-governed] {gene} blocked: {decision.failures}")
            return 1
        decision = engine.apply(decision)
        if not decision.passed:
            return 1
        print(f"[alt21-governed] {gene} -> governed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
