"""Continuity Substrate Organ — continuity and preference profile posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-CSO-01"
ORGAN_VERSION = "continuity_substrate_organ.v1"


def build_continuity_substrate_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    continuity_present = (root / "src" / "continuity_profile.py").is_file()
    preference_present = (root / "src" / "preference_profile.py").is_file()
    summary = (
        f"continuity={int(continuity_present)};"
        f"preference={int(preference_present)};read_only=1"
    )[:128]
    return {
        "continuity_substrate_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "continuity_profile_present": continuity_present,
        "preference_profile_present": preference_present,
        "substrate_aligned": continuity_present and preference_present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
