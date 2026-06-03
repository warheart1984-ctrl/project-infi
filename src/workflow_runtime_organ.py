"""Workflow Runtime Organ — app workflow_runtime posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-WRT-01"
ORGAN_VERSION = "workflow_runtime_organ.v1"


def build_workflow_runtime_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "app" / "workflow_runtime.py").is_file()
    return {
        "workflow_runtime_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"workflow_runtime={int(present)};read_only=1"[:128],
        "workflow_runtime_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
