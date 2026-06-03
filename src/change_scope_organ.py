"""Change Scope Organ — read-only workspace impact posture."""

# Mythic: Change Scope Organ
# Engineering: ChangeScopeEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-CS-01"
ORGAN_VERSION = "change_scope_organ.v1"


def build_change_scope_status(*, root: Path | None = None) -> dict[str, Any]:
    """Bounded change-scope module posture."""
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "src" / "change_scope.py").is_file()
    workbench_present = (root / "src" / "evolving_workbench.py").is_file()
    summary = f"change_scope={present};workbench={workbench_present}"[:128]
    return {
        "change_scope_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "change_scope_present": present,
        "workspace_intel_present": workbench_present,
        "impact_analysis_available": present and workbench_present,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
