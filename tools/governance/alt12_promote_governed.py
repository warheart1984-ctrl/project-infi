#!/usr/bin/env python3
"""Promote Alt-12 organs from MVP to governed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

ALT12_GOVERNED = {
    gene: f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md"
    for gene in (
        "otem_bounded_organ",
        "direct_challenge_organ",
        "orchestration_spine_organ",
        "operator_health_sentinel_organ",
        "governed_realtime_lane_organ",
        "v8_runtime_organ",
        "patch_apply_organ",
        "patch_execution_preview_organ",
        "run_ledger_organ",
    )
}

ELIGIBILITY = _ROOT / "tools/governance/check_alt12_governed_eligibility.py"


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
        print("[alt12-governed] eligibility gate failed")
        return 1

    engine = PromotionEngine(_ROOT)
    for gene, proof in ALT12_GOVERNED.items():
        prepare_governed(gene, proof)
        decision = engine.evaluate(gene, run_gates=True)
        if not decision.passed or decision.target_stage != "governed":
            print(f"[alt12-governed] {gene} blocked: {decision.failures}")
            return 1
        decision = engine.apply(decision)
        if not decision.passed:
            print(f"[alt12-governed] {gene} apply failed: {decision.failures}")
            return 1
        print(f"[alt12-governed] {gene} -> governed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
