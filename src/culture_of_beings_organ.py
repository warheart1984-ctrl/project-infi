"""Culture-of-Beings Organ — live posture from culture-of-beings runtime."""

from __future__ import annotations

from typing import Any


def build_culture_of_beings_status() -> dict[str, Any]:
    try:
        from src.culture_of_beings_runtime import culture_of_beings_runtime

        posture = culture_of_beings_runtime.culture_of_beings_posture()
        return {
            "culture_of_beings_organ_version": "culture_of_beings_organ.v1",
            "adopted_norms": posture.get("adopted_norms", 0),
            "candidate_norms": posture.get("candidate_norms", 0),
            "culture_of_beings_drift_events": posture.get("culture_of_beings_drift_events", 0),
            "cluster_norm_count": posture.get("cluster_norm_count", 0),
            "identity_aligned": posture.get("identity_aligned", True),
            "pact_aligned": posture.get("pact_aligned", True),
            "cisiv_stage": "implementation",
            "claim_label": str(posture.get("claim_label") or "asserted"),
            "read_only": True,
            "live_runtime": True,
        }
    except Exception as exc:
        return {
            "culture_of_beings_organ_version": "culture_of_beings_organ.v1",
            "adopted_norms": 0,
            "candidate_norms": 0,
            "culture_of_beings_drift_events": 0,
            "cisiv_stage": "implementation",
            "claim_label": "rejected",
            "read_only": True,
            "error": str(exc)[:200],
        }
