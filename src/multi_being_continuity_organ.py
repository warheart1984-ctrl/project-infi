"""Multi-Being Continuity Organ — live posture from multi-being continuity runtime."""

# Mythic: Multi-Being Continuity Organ
# Engineering: MultiBeingContinuityEngine
from __future__ import annotations

from typing import Any


def build_multi_being_continuity_status() -> dict[str, Any]:
    """Read-only multi-being posture from live runtime."""
    try:
        from src.multi_being_continuity_runtime import multi_being_continuity_runtime

        posture = multi_being_continuity_runtime.multi_being_posture()
        snapshot = multi_being_continuity_runtime.multi_being_snapshot()
        federation = dict(snapshot.get("federation_summary") or {})
        return {
            "multi_being_continuity_organ_version": "multi_being_continuity_organ.v1",
            "adopted_pacts": posture.get("adopted_pacts", 0),
            "candidate_pacts": posture.get("candidate_pacts", 0),
            "multi_being_drift_events": posture.get("multi_being_drift_events", 0),
            "cross_organism_peer_count": posture.get("cross_organism_peer_count", 0),
            "digest_verified_count": posture.get("digest_verified_count", 0),
            "accepted_grant_count": int(federation.get("accepted_grant_count") or 0),
            "identity_aligned": posture.get("identity_aligned", True),
            "narrative_aligned": posture.get("narrative_aligned", True),
            "agency_aligned": posture.get("agency_aligned", True),
            "social_aligned": posture.get("social_aligned", True),
            "cisiv_stage": "implementation",
            "claim_label": str(posture.get("claim_label") or "asserted"),
            "read_only": True,
            "live_runtime": True,
        }
    except Exception as exc:
        return {
            "multi_being_continuity_organ_version": "multi_being_continuity_organ.v1",
            "adopted_pacts": 0,
            "candidate_pacts": 0,
            "multi_being_drift_events": 0,
            "cross_organism_peer_count": 0,
            "digest_verified_count": 0,
            "cisiv_stage": "implementation",
            "claim_label": "rejected",
            "read_only": True,
            "error": str(exc)[:200],
        }
