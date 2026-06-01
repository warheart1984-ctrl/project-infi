"""Slingshot preload adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from slingshot.frame import build_slingshot_frame
from slingshot.packet import build_slingshot_packet


def run_slingshot_preload(
    *,
    case_id: str,
    repo_path: str,
    trace_path: str = "",
) -> dict[str, Any]:
    frame = build_slingshot_frame(case_id=case_id, repo_path=repo_path, trace_path=trace_path)
    packet = build_slingshot_packet(frame)
    return {
        "case_id": case_id,
        "frame": frame,
        "packet": packet,
        "launch_blocked": bool(frame.get("launch_blocked")),
        "artifact_dir": str(Path(".runtime/slingshot") / case_id),
        "mechanic_case_dir": str(Path(".runtime/mechanic") / case_id),
    }
