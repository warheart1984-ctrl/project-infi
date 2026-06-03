"""Linguistic Work Order History Subsystem — Wave 17 snapshot retention."""

# Mythic: Linguistic Work Order History Organ
# Engineering: LinguisticWorkOrderHistoryEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LWOH-01"
ORGAN_VERSION = "linguistic_work_order_history_organ.v1"


def build_linguistic_work_order_history_status(
    *, root: Path | None = None
) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    from src.governance_organs.linguistic_governance_work_order_engine import (
        list_work_order_snapshots,
        work_order_snapshots_dir,
    )

    snap_dir = work_order_snapshots_dir(root)
    snaps = list_work_order_snapshots(root)
    return {
        "linguistic_work_order_history_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"snapshots={len(snaps)}"[:128],
        "snapshot_dir_present": snap_dir.is_dir(),
        "snapshot_count": len(snaps),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
