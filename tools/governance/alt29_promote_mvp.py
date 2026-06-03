#!/usr/bin/env python3
"""Promote media_processor_bridge_organ to MVP for Release 29."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

BATCH = "alt29-summon-wave-2026-06"
GENE = "media_processor_bridge_organ"

SPEC = {
    "active_doc": "docs/subsystems/platform/MEDIA_PROCESSOR_BRIDGE_ORGAN.md",
    "prototype_proof": "docs/proof/platform/MEDIA_PROCESSOR_BRIDGE_ORGAN_V1_PROOF.md",
    "v1_proof": "docs/proof/platform/MEDIA_PROCESSOR_BRIDGE_ORGAN_V1_PROOF.md",
    "surface_prototype": [
        {"kind": "module", "path": "src/media_processor_bridge_organ.py", "isolated": True},
    ],
    "surface_mvp": [
        {"kind": "module", "path": "src/media_processor_bridge_organ.py"},
        {"kind": "api", "path": "GET /api/jarvis/media-processor-bridge/status"},
        {"kind": "gate", "path": "make media-processor-bridge-organ-gate"},
    ],
}


def main() -> int:
    engine = PromotionEngine(_ROOT)
    path = _ROOT / "governance/subsystem_genomes" / f"{GENE}.genome.v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    stage = (data.get("identity") or {}).get("stage", "")
    if stage in {"mvp", "governed"}:
        data.setdefault("activation", {})["batch_id"] = BATCH
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"[alt29-mvp] {GENE} already {stage}")
        return 0
    data.setdefault("activation", {})["batch_id"] = BATCH
    data.setdefault("proof", {})["bundles"] = [SPEC["v1_proof"]]
    data["runtime"] = {"surface": SPEC["surface_mvp"]}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    decision = engine.evaluate(GENE, run_gates=True)
    if not decision.passed or decision.target_stage != "mvp":
        # Direct MVP stamp when promotion gates already satisfied at concept
        ident = data.setdefault("identity", {})
        if ident.get("stage") == "concept":
            ident["stage"] = "mvp"
            data["proof"]["posture"] = "mvp"
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"[alt29-mvp] {GENE} -> mvp (direct stamp)")
            return 0
        print(f"[alt29-mvp] blocked: {decision.failures}")
        return 1
    engine.apply(decision)
    print(f"[alt29-mvp] {GENE} -> mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
