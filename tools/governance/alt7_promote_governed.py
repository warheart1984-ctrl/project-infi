#!/usr/bin/env python3
"""Promote Alt-7 operator_cognition_coherence_fabric from MVP to governed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

GENE = "operator_cognition_coherence_fabric"
GOVERNED_PROOF = "docs/proof/platform/OPERATOR_COGNITION_COHERENCE_FABRIC_GOVERNED_PROOF.md"
ELIGIBILITY = _ROOT / "tools/governance/check_alt7_governed_eligibility.py"


def _load() -> dict:
    path = _ROOT / "governance/subsystem_genomes" / f"{GENE}.genome.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    path = _ROOT / "governance/subsystem_genomes" / f"{GENE}.genome.v1.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def prepare_governed() -> None:
    data = _load()
    data.setdefault("proof", {})["bundles"] = [GOVERNED_PROOF]
    _save(data)


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(ELIGIBILITY)],
        cwd=_ROOT,
        check=False,
    )
    if proc.returncode != 0:
        print("[alt7-governed] eligibility gate failed — run make alt7-governed-gate")
        return 1

    prepare_governed()
    engine = PromotionEngine(_ROOT)
    decision = engine.evaluate(GENE, run_gates=True)
    if not decision.passed or decision.target_stage != "governed":
        print(f"[alt7-governed] {GENE} blocked: {decision.failures}")
        return 1
    decision = engine.apply(decision)
    if not decision.passed:
        print(f"[alt7-governed] {GENE} apply failed: {decision.failures}")
        return 1
    print(f"[alt7-governed] {GENE} -> governed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
