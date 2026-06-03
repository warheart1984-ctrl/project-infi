"""Safety Envelope Organ — read-only threshold snapshot from SWARM_LAW doctrine."""

# Mythic: Safety Envelope
# Engineering: SafetyEnvelopeEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

SWARM_LAW_PATH = Path("docs/contracts/SWARM_LAW.md")

DEFAULT_THRESHOLDS = {
    "uncertainty_max": 0.35,
    "comms_degraded": False,
    "halt_required": False,
}


def load_swarm_law_excerpt(root: Path | None = None) -> str:
    root = root or Path(__file__).resolve().parents[1]
    path = root / SWARM_LAW_PATH
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    if "safety envelope" in text.lower():
        start = text.lower().index("safety envelope")
        return text[start : start + 400]
    return text[:400]


def build_envelope_status(*, root: Path | None = None) -> dict[str, Any]:
    thresholds = dict(DEFAULT_THRESHOLDS)
    excerpt = load_swarm_law_excerpt(root)
    if "halt" in excerpt.lower():
        thresholds["halt_required"] = "crossed" in excerpt.lower()
    return {
        "safety_envelope_organ_version": "safety_envelope_organ.v1",
        "envelope_id": "default",
        "thresholds": thresholds,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "source_contract": str(SWARM_LAW_PATH),
        "read_only": True,
    }
