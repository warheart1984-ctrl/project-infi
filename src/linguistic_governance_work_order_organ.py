"""Linguistic Governance Work Order Subsystem — Wave 14 operator execution posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LWO-01"
ORGAN_VERSION = "linguistic_governance_work_order_organ.v1"


def build_linguistic_governance_work_order_status(
    *, root: Path | None = None
) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_governance_work_order_engine.py"
    ).is_file()
    wo_dir = root / "governance" / "linguistic_governance_work_orders"
    wo_count = len(list(wo_dir.glob("*.v1.json"))) if wo_dir.is_dir() else 0
    cli = (root / "tools" / "governance" / "linguistic_work_order.py").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    return {
        "linguistic_governance_work_order_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};orders={wo_count}"[:128],
        "work_order_engine_present": engine,
        "work_orders_dir_present": wo_dir.is_dir(),
        "work_order_artifact_count": wo_count,
        "work_order_cli_present": cli,
        "linguistic_work_order_sync_in_makefile": (
            "linguistic-work-order-sync:" in m_text
        ),
        "linguistic_work_order_gate_in_makefile": (
            "linguistic-work-order-gate:" in m_text
        ),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
