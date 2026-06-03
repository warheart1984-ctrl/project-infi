"""Workflow Interfaces Subsystem — workflow UI posture."""

# Mythic: Workflow Interfaces Organ
# Engineering: WorkflowInterfacesInterface
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-WIF-01"
ORGAN_VERSION = "workflow_interfaces_organ.v1"

_WORKFLOW_PAGES = (
    "WorkflowBuilder.jsx",
    "WorkflowRuns.jsx",
    "WorkflowApprovals.jsx",
    "WorkflowTemplates.jsx",
)


def build_workflow_interfaces_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    pages = root / "frontend" / "src" / "pages"
    present = sum(1 for name in _WORKFLOW_PAGES if (pages / name).is_file())
    return {
        "workflow_interfaces_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"workflow_pages={present};read_only=1"[:128],
        "workflow_pages_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
