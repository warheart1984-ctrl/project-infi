"""Linguistic Governance Queue Subsystem — Wave 13 queue + Wave 14 work orders."""

# Mythic: Linguistic Governance Queue Organ
# Engineering: LinguisticGovernanceQueueEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LGQ-01"
ORGAN_VERSION = "linguistic_governance_queue_organ.v1"


def build_linguistic_governance_queue_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_governance_queue_engine.py"
    ).is_file()
    wo_engine = (
        root / "src" / "governance_organs" / "linguistic_governance_work_order_engine.py"
    ).is_file()
    queue = (root / "governance" / "linguistic_governance_queue.v1.json").is_file()
    wo_dir = (root / "governance" / "linguistic_governance_work_orders").is_dir()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    return {
        "linguistic_governance_queue_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": (
            f"queue={int(queue)};work_orders={int(wo_dir)};engine={int(engine)}"
        )[:128],
        "queue_engine_present": engine,
        "work_order_engine_present": wo_engine,
        "governance_queue_present": queue,
        "work_orders_dir_present": wo_dir,
        "linguistic_governance_queue_in_makefile": "linguistic-governance-queue:" in m_text,
        "linguistic_work_order_sync_in_makefile": "linguistic-work-order-sync:" in m_text,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
