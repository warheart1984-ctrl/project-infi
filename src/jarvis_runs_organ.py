"""Jarvis Runs Subsystem — runs API posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-JRN-01"
ORGAN_VERSION = "jarvis_runs_organ.v1"


def build_jarvis_runs_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    api = root / "src" / "api.py"
    text = api.read_text(encoding="utf-8") if api.is_file() else ""
    present = "/api/jarvis/runs" in text
    return {
        "jarvis_runs_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"runs_api={int(present)};read_only=1"[:128],
        "runs_api_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
