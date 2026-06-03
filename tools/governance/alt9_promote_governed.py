#!/usr/bin/env python3
"""Promote Alt-9 infrastructure organs from MVP to governed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

ALT9_GOVERNED = {
    "phase_gate_organ": "docs/proof/platform/PHASE_GATE_ORGAN_GOVERNED_PROOF.md",
    "realtime_event_cause_predictor_organ": "docs/proof/platform/REALTIME_EVENT_CAUSE_PREDICTOR_ORGAN_GOVERNED_PROOF.md",
    "invariant_engine_organ": "docs/proof/platform/INVARIANT_ENGINE_ORGAN_GOVERNED_PROOF.md",
}

ELIGIBILITY = _ROOT / "tools/governance/check_alt9_governed_eligibility.py"


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
        print("[alt9-governed] eligibility gate failed")
        return 1

    engine = PromotionEngine(_ROOT)
    for gene, proof in ALT9_GOVERNED.items():
        prepare_governed(gene, proof)
        decision = engine.evaluate(gene, run_gates=True)
        if not decision.passed or decision.target_stage != "governed":
            print(f"[alt9-governed] {gene} blocked: {decision.failures}")
            return 1
        decision = engine.apply(decision)
        if not decision.passed:
            print(f"[alt9-governed] {gene} apply failed: {decision.failures}")
            return 1
        print(f"[alt9-governed] {gene} -> governed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
