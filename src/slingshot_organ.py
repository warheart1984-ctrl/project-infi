"""Slingshot Organ — read-only kinetic accelerator posture."""

# Mythic: Slingshot Organ
# Engineering: SlingshotEngine
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-SLO-01"
ORGAN_VERSION = "slingshot_organ.v1"
_DEFAULT_CASE = os.environ.get("SLINGSHOT_STATUS_CASE_ID", "demo")


def build_slingshot_status(*, case_id: str | None = None, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    case = str(case_id or _DEFAULT_CASE).strip() or "demo"
    runtime_root = root / ".runtime" / "slingshot" / case
    frame_present = False
    packet_present = False
    launch_blocked = True
    drift_count = 0
    try:
        from slingshot.common import frame_path, packet_path, slingshot_case_dir
        from slingshot.frame import load_slingshot_frame

        runtime_root = slingshot_case_dir(case)
        frame_present = frame_path(case).is_file()
        packet_present = packet_path(case).is_file()
        if frame_present:
            frame = load_slingshot_frame(case)
            launch_blocked = bool(frame.get("launch_blocked"))
            drift_count = int(frame.get("drift_count") or 0)
    except Exception:
        runtime_root = root / ".runtime" / "slingshot" / case

    summary = (
        f"case={case};frame={int(frame_present)};blocked={int(launch_blocked)};read_only=1"
    )[:128]
    return {
        "slingshot_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "case_id": case,
        "runtime_case_dir": str(runtime_root),
        "frame_present": frame_present,
        "packet_present": packet_present,
        "launch_blocked": launch_blocked,
        "drift_count": drift_count,
        "ma13_enforced": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
