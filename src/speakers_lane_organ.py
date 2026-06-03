"""Speakers Lane Organ — read-only Speakers mix lane posture."""

# Mythic: Speakers Lane Organ
# Engineering: SpeakersLaneInterface
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-SPL-01"
ORGAN_VERSION = "speakers_lane_organ.v1"


def build_speakers_lane_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    speakers_root = root / "external/beatbox_speakers/src/speakers"
    contracts_present = (speakers_root / "contracts.py").is_file()
    summary = f"contracts={int(contracts_present)};chain_lane=speakers;bridge_safe=1"[:128]
    return {
        "speakers_lane_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "contracts_present": contracts_present,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
