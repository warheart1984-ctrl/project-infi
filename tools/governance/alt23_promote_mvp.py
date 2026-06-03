#!/usr/bin/env python3
"""Promote Release 23 concept schemas through prototype to MVP."""

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


ALT23_GENES = {
    "linguistic_drift_forecast_organ": _entry(
        "linguistic_drift_forecast_organ",
        "linguistic-drift-forecast",
        "linguistic-drift-forecast-organ-gate",
    ),
    "linguistic_preemptive_remediation_organ": _entry(
        "linguistic_preemptive_remediation_organ",
        "linguistic-preemptive-remediation",
        "linguistic-preemptive-remediation-organ-gate",
    ),
    "linguistic_predictive_governance_organ": _entry(
        "linguistic_predictive_governance_organ",
        "linguistic-predictive-governance",
        "linguistic-predictive-governance-organ-gate",
    ),
    "linguistic_predictive_cycle_history_organ": _entry(
        "linguistic_predictive_cycle_history_organ",
        "linguistic-predictive-cycle-history",
        "linguistic-predictive-cycle-history-organ-gate",
    ),
    "linguistic_governance_cycle_organ": _entry(
        "linguistic_governance_cycle_organ",
        "linguistic-governance-cycle",
        "linguistic-governance-cycle-organ-gate",
    ),
    "linguistic_governance_cycle_history_organ": _entry(
        "linguistic_governance_cycle_history_organ",
        "linguistic-governance-cycle-history",
        "linguistic-governance-cycle-history-organ-gate",
    ),
    "linguistic_forecast_consumption_organ": _entry(
        "linguistic_forecast_consumption_organ",
        "linguistic-forecast-consumption",
        "linguistic-forecast-consumption-organ-gate",
    ),
    "linguistic_cycle_optimization_organ": _entry(
        "linguistic_cycle_optimization_organ",
        "linguistic-cycle-optimization",
        "linguistic-cycle-optimization-organ-gate",
    ),
    "linguistic_closed_loop_fabric_organ": _entry(
        "linguistic_closed_loop_fabric_organ",
        "linguistic-closed-loop-fabric",
        "linguistic-closed-loop-fabric-organ-gate",
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
    for gene, spec in ALT23_GENES.items():
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt23] {gene} prototype blocked: {d1.failures}")
            return 1
        d1_apply = engine.apply(d1)
        if not d1_apply.passed:
            print(f"[alt23] {gene} prototype apply failed: {d1_apply.failures}")
            return 1
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt23] {gene} mvp blocked: {d2.failures}")
            return 1
        engine.apply(d2)
        print(f"[alt23] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
