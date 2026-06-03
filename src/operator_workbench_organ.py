"""Operator Workbench Organ — read-only evolving workbench posture."""

# Mythic: Operator Workbench Organ
# Engineering: OperatorWorkbenchEngine
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-OWO-01"
ORGAN_VERSION = "operator_workbench_organ.v1"


def build_operator_workbench_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    module_present = (root / "src" / "evolving_workbench.py").is_file()
    primary = os.environ.get("AAIS_PRIMARY_PROJECT", "").strip()
    summary = (
        f"module={int(module_present)};proposal_only=1;primary_set={int(bool(primary))}"
    )[:128]
    return {
        "operator_workbench_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "workbench_module_present": module_present,
        "primary_project_env_set": bool(primary),
        "proposal_only": True,
        "patch_apply_via_organ": False,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
