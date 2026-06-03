"""Operator Console Interface Subsystem — operator console UI posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-OCI-01"
ORGAN_VERSION = "operator_console_interface_organ.v1"


def build_operator_console_interface_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "frontend" / "src" / "pages" / "OperatorConsole.jsx").is_file()
    return {
        "operator_console_interface_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"operator_console_ui={int(present)};read_only=1"[:128],
        "operator_console_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
