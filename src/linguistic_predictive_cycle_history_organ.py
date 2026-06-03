"""Linguistic Predictive Cycle History Subsystem — predictive cycle artifact retention."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LPH-01"
ORGAN_VERSION = "linguistic_predictive_cycle_history_organ.v1"


def build_linguistic_predictive_cycle_history_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    cycle_dir = root / "governance" / "linguistic_predictive_cycles"
    count = len(list(cycle_dir.glob("*.json"))) if cycle_dir.is_dir() else 0
    policy = (
        root / "governance" / "linguistic_predictive_governance_policy.v1.json"
    ).is_file()
    retain = 0
    if policy:
        import json

        data = json.loads(
            (root / "governance" / "linguistic_predictive_governance_policy.v1.json").read_text(
                encoding="utf-8"
            )
        )
        retain = int(data.get("retain_predictive_cycle_history", 0))
    return {
        "linguistic_predictive_cycle_history_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"artifacts={count};retain={retain}"[:128],
        "predictive_cycle_artifact_count": count,
        "retain_predictive_cycle_history": retain,
        "predictive_cycles_dir_present": cycle_dir.is_dir(),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
