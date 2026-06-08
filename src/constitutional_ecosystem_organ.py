"""Constitutional Ecosystem Organ — live posture from ecosystem runtime."""

from __future__ import annotations

from typing import Any


def build_constitutional_ecosystem_status() -> dict[str, Any]:
    try:
        from src.constitutional_ecosystem_runtime import constitutional_ecosystem_runtime

        posture = constitutional_ecosystem_runtime.ecosystem_posture()
        return {
            "constitutional_ecosystem_organ_version": "constitutional_ecosystem_organ.v1",
            "adopted_charters": posture.get("adopted_charters", 0),
            "candidate_charters": posture.get("candidate_charters", 0),
            "ecosystem_drift_events": posture.get("ecosystem_drift_events", 0),
            "member_pact_count": posture.get("member_pact_count", 0),
            "cisiv_stage": "implementation",
            "claim_label": str(posture.get("claim_label") or "asserted"),
            "read_only": True,
            "live_runtime": True,
        }
    except Exception as exc:
        return {
            "constitutional_ecosystem_organ_version": "constitutional_ecosystem_organ.v1",
            "adopted_charters": 0,
            "candidate_charters": 0,
            "ecosystem_drift_events": 0,
            "cisiv_stage": "implementation",
            "claim_label": "rejected",
            "read_only": True,
            "error": str(exc)[:200],
        }
