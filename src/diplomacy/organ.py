"""Inter-substrate diplomacy organ — live runtime posture for organ mesh (Stage 15)."""

from __future__ import annotations

from typing import Any


def build_inter_substrate_diplomacy_status() -> dict[str, Any]:
    from src.diplomacy.runtime import inter_substrate_diplomacy_runtime

    try:
        posture = inter_substrate_diplomacy_runtime.diplomacy_posture()
    except Exception:
        posture = {"claim_label": "rejected", "adopted_accords": 0}
    return {
        "organ_id": "inter_substrate_diplomacy",
        "organ_kind": "civilizational_diplomacy",
        "posture": posture,
        "claim_label": posture.get("claim_label", "asserted"),
    }
