#!/usr/bin/env python3
"""Promote Release 25 concept schemas through prototype to MVP."""

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


ALT25_GENES = {
    "linguistic_forecast_archive_organ": _entry(
        "linguistic_forecast_archive_organ",
        "linguistic-forecast-archive",
        "linguistic-forecast-archive-organ-gate",
    ),
    "linguistic_drift_report_organ": _entry(
        "linguistic_drift_report_organ",
        "linguistic-drift-report",
        "linguistic-drift-report-organ-gate",
    ),
    "linguistic_governance_work_order_organ": _entry(
        "linguistic_governance_work_order_organ",
        "linguistic-governance-work-order",
        "linguistic-governance-work-order-organ-gate",
    ),
    "linguistic_governance_cadence_organ": _entry(
        "linguistic_governance_cadence_organ",
        "linguistic-governance-cadence",
        "linguistic-governance-cadence-organ-gate",
    ),
    "linguistic_forecast_calibration_report_organ": _entry(
        "linguistic_forecast_calibration_report_organ",
        "linguistic-forecast-calibration-report",
        "linguistic-forecast-calibration-report-organ-gate",
    ),
    "linguistic_full_governance_cycle_history_organ": _entry(
        "linguistic_full_governance_cycle_history_organ",
        "linguistic-full-governance-cycle-history",
        "linguistic-full-governance-cycle-history-organ-gate",
    ),
    "meta_linguistic_registry_organ": _entry(
        "meta_linguistic_registry_organ",
        "meta-linguistic-registry",
        "meta-linguistic-registry-organ-gate",
    ),
    "linguistic_subsystem_promotion_organ": _entry(
        "linguistic_subsystem_promotion_organ",
        "linguistic-subsystem-promotion",
        "linguistic-subsystem-promotion-organ-gate",
    ),
    "linguistic_governed_lifecycle_fabric_organ": _entry(
        "linguistic_governed_lifecycle_fabric_organ",
        "linguistic-governed-lifecycle-fabric",
        "linguistic-governed-lifecycle-fabric-organ-gate",
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
    for gene, spec in ALT25_GENES.items():
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt25] {gene} prototype blocked: {d1.failures}")
            return 1
        d1_apply = engine.apply(d1)
        if not d1_apply.passed:
            print(f"[alt25] {gene} prototype apply failed: {d1_apply.failures}")
            return 1
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt25] {gene} mvp blocked: {d2.failures}")
            return 1
        engine.apply(d2)
        print(f"[alt25] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
