"""Beatbox Lane Organ — read-only Beatbox score lane posture."""

# Mythic: Beatbox Lane Organ
# Engineering: BeatboxLaneInterface
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-BBL-01"
ORGAN_VERSION = "beatbox_lane_organ.v1"


def build_beatbox_lane_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    beatbox_root = root / "external/beatbox_speakers/src/beatbox"
    contracts_present = (beatbox_root / "contracts.py").is_file()
    summary = f"contracts={int(contracts_present)};chain_lane=beatbox;bridge_safe=1"[:128]
    return {
        "beatbox_lane_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "contracts_present": contracts_present,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
