"""Social Continuity Organ — live posture from social continuity runtime."""

# Mythic: Social Continuity Organ
# Engineering: SocialContinuityEngine
from __future__ import annotations

from typing import Any


def build_social_continuity_status() -> dict[str, Any]:
    """Read-only social posture from live runtime."""
    try:
        from src.social_continuity_runtime import social_continuity_runtime

        posture = social_continuity_runtime.social_posture()
        snapshot = social_continuity_runtime.social_snapshot()
        federation = dict(snapshot.get("federation_summary") or {})
        federated_count = int(federation.get("accepted_grant_count") or posture.get("federated_peer_count") or 0)
        return {
            "social_continuity_organ_version": "social_continuity_organ.v1",
            "adopted_bonds": posture.get("adopted_bonds", 0),
            "candidate_bonds": posture.get("candidate_bonds", 0),
            "social_drift_events": posture.get("social_drift_events", 0),
            "federated_peer_count": federated_count,
            "identity_aligned": posture.get("identity_aligned", True),
            "narrative_aligned": posture.get("narrative_aligned", True),
            "agency_aligned": posture.get("agency_aligned", True),
            "cisiv_stage": "implementation",
            "claim_label": str(posture.get("claim_label") or "asserted"),
            "read_only": True,
            "live_runtime": True,
        }
    except Exception as exc:
        return {
            "social_continuity_organ_version": "social_continuity_organ.v1",
            "adopted_bonds": 0,
            "candidate_bonds": 0,
            "social_drift_events": 0,
            "federated_peer_count": 0,
            "cisiv_stage": "implementation",
            "claim_label": "rejected",
            "read_only": True,
            "error": str(exc)[:200],
        }
