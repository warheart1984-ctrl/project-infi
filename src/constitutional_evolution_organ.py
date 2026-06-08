"""Constitutional evolution organ — live runtime posture (Stage 17)."""

from __future__ import annotations

from typing import Any


def build_constitutional_evolution_status() -> dict[str, Any]:
    from src.constitutional_evolution_runtime import constitutional_evolution_runtime

    try:
        posture = constitutional_evolution_runtime.evolution_posture()
    except Exception:
        posture = {"claim_label": "rejected", "adopted_amendments": 0}
    return {
        "organ_id": "constitutional_evolution",
        "organ_kind": "civilizational_evolution",
        "posture": posture,
        "claim_label": posture.get("claim_label", "asserted"),
    }
