"""Workflow Shell Organ — read-only FastAPI workflow shell posture."""

# Mythic: Workflow Shell Organ
# Engineering: WorkflowShellEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-WSO-01"
ORGAN_VERSION = "workflow_shell_organ.v1"


def build_workflow_shell_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    main_present = (root / "app" / "main.py").is_file()
    runtime_present = (root / "app" / "workflow_runtime.py").is_file()
    shell_surface = "workflow_shell"
    summary = (
        f"main={int(main_present)};runtime={int(runtime_present)};surface={shell_surface}"
    )[:128]
    return {
        "workflow_shell_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "app_main_present": main_present,
        "workflow_runtime_present": runtime_present,
        "shell_surface": shell_surface,
        "legacy_flask_bridge_transition": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
