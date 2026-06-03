#!/usr/bin/env python3
"""Complete Release 24 MVP surfaces and active docs (Wave 15)."""

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


ALT24_GENES = {
    "linguistic_forecast_calibration_organ": _entry(
        "linguistic_forecast_calibration_organ",
        "linguistic-forecast-calibration",
        "linguistic-forecast-calibration-organ-gate",
    ),
    "linguistic_governance_queue_organ": _entry(
        "linguistic_governance_queue_organ",
        "linguistic-governance-queue",
        "linguistic-governance-queue-organ-gate",
    ),
    "linguistic_full_governance_cycle_organ": _entry(
        "linguistic_full_governance_cycle_organ",
        "linguistic-full-governance-cycle",
        "linguistic-full-governance-cycle-organ-gate",
    ),
    "linguistic_governance_attestation_organ": _entry(
        "linguistic_governance_attestation_organ",
        "linguistic-governance-attestation",
        "linguistic-governance-attestation-organ-gate",
    ),
}


def _load(gene: str) -> dict:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _save(gene: str, data: dict) -> None:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def prepare_mvp(gene: str, spec: dict) -> None:
    data = _load(gene)
    data.setdefault("runtime", {})["surface"] = spec["surface_mvp"]
    data.setdefault("proof", {})["bundles"] = [spec["v1_proof"]]
    data.setdefault("ssp", {})["active_doc"] = spec["active_doc"]
    data.setdefault("ssp", {})["summon_eligible"] = False
    _save(gene, data)


def main() -> int:
    engine = PromotionEngine(_ROOT)
    for gene, spec in ALT24_GENES.items():
        stage = (_load(gene).get("identity") or {}).get("stage", "")
        prepare_mvp(gene, spec)
        if stage == "mvp":
            print(f"[alt24-mvp] {gene} surfaces updated (already mvp)")
            continue
        if stage == "governed":
            print(f"[alt24-mvp] {gene} surfaces updated (governed — skip promotion)")
            continue
        prepare_prototype_surface = spec["surface_prototype"]
        data = _load(gene)
        data.setdefault("runtime", {})["surface"] = prepare_prototype_surface
        _save(gene, data)
        d1 = engine.evaluate(gene)
        if d1.passed and d1.target_stage:
            engine.apply(d1)
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt24-mvp] {gene} mvp blocked: {d2.failures}")
            return 1
        if d2.target_stage:
            engine.apply(d2)
        print(f"[alt24-mvp] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
