"""Multi-Organism Governance Membrane Organ — live posture from membrane runtime."""

# Engineering: GovernanceMembraneEngine

from __future__ import annotations

from typing import Any


def build_governance_membrane_status() -> dict[str, Any]:
    try:
        from src.multi_organism_governance_membrane_runtime import multi_organism_governance_membrane_runtime

        posture = multi_organism_governance_membrane_runtime.membrane_posture()
        return {
            "governance_membrane_organ_version": "governance_membrane_organ.v1",
            "adopted_policies": posture.get("adopted_policies", 0),
            "candidate_policies": posture.get("candidate_policies", 0),
            "membrane_drift_events": posture.get("membrane_drift_events", 0),
            "permeability_channels": posture.get("permeability_channels", 0),
            "cisiv_stage": "implementation",
            "claim_label": str(posture.get("claim_label") or "asserted"),
            "read_only": True,
            "live_runtime": True,
        }
    except Exception as exc:
        return {
            "governance_membrane_organ_version": "governance_membrane_organ.v1",
            "adopted_policies": 0,
            "candidate_policies": 0,
            "membrane_drift_events": 0,
            "cisiv_stage": "implementation",
            "claim_label": "rejected",
            "read_only": True,
            "error": str(exc)[:200],
        }
