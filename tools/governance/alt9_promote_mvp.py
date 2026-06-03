#!/usr/bin/env python3
"""Promote Alt-9 concept genomes through prototype to MVP."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

ALT9_GENES = {
    "phase_gate_organ": {
        "active_doc": "docs/subsystems/platform/PHASE_GATE_ORGAN.md",
        "prototype_proof": "docs/proof/platform/PHASE_GATE_ORGAN_V1_PROOF.md",
        "v1_proof": "docs/proof/platform/PHASE_GATE_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/phase_gate_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/phase_gate_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/phase-gate/status"},
            {"kind": "gate", "path": "make phase-gate-organ-gate"},
        ],
    },
    "realtime_event_cause_predictor_organ": {
        "active_doc": "docs/subsystems/platform/REALTIME_EVENT_CAUSE_PREDICTOR_ORGAN.md",
        "prototype_proof": "docs/proof/platform/REALTIME_EVENT_CAUSE_PREDICTOR_ORGAN_V1_PROOF.md",
        "v1_proof": "docs/proof/platform/REALTIME_EVENT_CAUSE_PREDICTOR_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {
                "kind": "module",
                "path": "src/realtime_event_cause_predictor_organ.py",
                "isolated": True,
            },
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/realtime_event_cause_predictor_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/realtime-predictor/status"},
            {"kind": "gate", "path": "make realtime-predictor-organ-gate"},
        ],
    },
    "invariant_engine_organ": {
        "active_doc": "docs/subsystems/platform/INVARIANT_ENGINE_ORGAN.md",
        "prototype_proof": "docs/proof/platform/INVARIANT_ENGINE_ORGAN_V1_PROOF.md",
        "v1_proof": "docs/proof/platform/INVARIANT_ENGINE_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/invariant_engine_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/invariant_engine_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/invariant-engine/status"},
            {"kind": "gate", "path": "make invariant-engine-organ-gate"},
        ],
    },
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
    for gene, spec in ALT9_GENES.items():
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt9] {gene} prototype blocked: {d1.failures}")
            return 1
        engine.apply(d1)
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt9] {gene} mvp blocked: {d2.failures}")
            return 1
        engine.apply(d2)
        print(f"[alt9] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
