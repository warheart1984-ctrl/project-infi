"""Linguistic Governance Cycle History Subsystem — governance cycle artifact retention."""

# Mythic: Linguistic Governance Cycle History Organ
# Engineering: LinguisticGovernanceCycleHistoryEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LGH-01"
ORGAN_VERSION = "linguistic_governance_cycle_history_organ.v1"


def build_linguistic_governance_cycle_history_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    cycle_dir = root / "governance" / "linguistic_governance_cycles"
    count = len(list(cycle_dir.glob("*.json"))) if cycle_dir.is_dir() else 0
    retain = 0
    policy_path = root / "governance" / "linguistic_governance_cycle_policy.v1.json"
    if policy_path.is_file():
        import json

        data = json.loads(policy_path.read_text(encoding="utf-8"))
        retain = int(data.get("retain_cycle_history", 0))
    return {
        "linguistic_governance_cycle_history_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"artifacts={count};retain={retain}"[:128],
        "governance_cycle_artifact_count": count,
        "retain_cycle_history": retain,
        "governance_cycles_dir_present": cycle_dir.is_dir(),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
