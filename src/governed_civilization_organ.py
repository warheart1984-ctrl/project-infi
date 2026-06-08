"""Governed civilization organ — live runtime posture (Stage 18)."""

from __future__ import annotations

from typing import Any


def build_governed_civilization_status() -> dict[str, Any]:
    from src.governed_civilization_runtime import governed_civilization_runtime

    try:
        posture = governed_civilization_runtime.civilization_posture()
    except Exception:
        posture = {"claim_label": "rejected", "adopted_civilizations": 0}
    return {
        "organ_id": "governed_civilization",
        "organ_kind": "civilizational_envelope",
        "posture": posture,
        "claim_label": posture.get("claim_label", "asserted"),
    }
