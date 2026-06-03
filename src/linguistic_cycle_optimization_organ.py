"""Linguistic Cycle Optimization Subsystem — cycle optimization recommendations posture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LCO-01"
ORGAN_VERSION = "linguistic_cycle_optimization_organ.v1"


def build_linguistic_cycle_optimization_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    rec_count = 0
    cycle_dir = root / "governance" / "linguistic_governance_cycles"
    if cycle_dir.is_dir():
        files = sorted(cycle_dir.glob("*.json"), reverse=True)
        if files:
            latest = json.loads(files[0].read_text(encoding="utf-8"))
            recs = latest.get("optimization_recommendations") or []
            rec_count = len(recs) if isinstance(recs, list) else 0
    engine = (
        root / "src" / "governance_organs" / "linguistic_governance_cycle_engine.py"
    ).is_file()
    return {
        "linguistic_cycle_optimization_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};recommendations={rec_count}"[:128],
        "governance_cycle_engine_present": engine,
        "last_optimization_recommendation_count": rec_count,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
