"""Norm federation organ — live runtime posture (Stage 16)."""

# Engineering: NormFederationEngine

from __future__ import annotations

from typing import Any


def build_norm_federation_status() -> dict[str, Any]:
    from src.norm_federation_runtime import norm_federation_runtime

    try:
        posture = norm_federation_runtime.federation_posture()
    except Exception:
        posture = {"claim_label": "rejected", "adopted_treaties": 0}
    return {
        "organ_id": "norm_federation",
        "organ_kind": "civilizational_federation",
        "posture": posture,
        "claim_label": posture.get("claim_label", "asserted"),
    }
