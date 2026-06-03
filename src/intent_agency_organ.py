"""Intent Agency Organ — read-only Nova intent/agency posture snapshot."""

# Mythic: Intent Agency Organ
# Engineering: IntentAgencyEngine
from __future__ import annotations

from typing import Any

from src.cog_runtime.intent_agency_evidence import run_agency_evidence_fixture


def _fixture_intents() -> tuple[dict[str, Any], dict[str, Any]]:
    prior = {
        "agency_note": "Operator continuity and proof discipline lead this arc.",
        "active_commitments": [
            {
                "commitment": "Finish cross-machine proof",
                "status": "active",
                "claim_posture": "proven",
            }
        ],
        "active_tensions": [
            {"poles": ["safety", "exploration"], "pull": "safety", "reason": "fixture"}
        ],
        "unified_closure": {
            "unified": True,
            "layers": [{"layer": "intent", "status": "aligned"}],
        },
    }
    next_intent = dict(prior)
    return prior, next_intent


def build_intent_agency_status() -> dict[str, Any]:
    """Read-only agency posture from proven evidence fixtures."""
    prior, next_intent = _fixture_intents()
    fixture = run_agency_evidence_fixture(
        prior_intent=prior,
        next_intent=next_intent,
        prior_narrative={"active_story": "Helping forge Wolf Cog OS"},
        next_narrative={"active_story": "Helping forge Wolf Cog OS"},
    )
    tensions = list(prior.get("active_tensions") or [])
    commitments = list(prior.get("active_commitments") or [])
    posture = fixture.get("claim_posture") or {}
    agency_claim = "proven" if fixture.get("passed") else str(posture.get("label") or "asserted")
    if agency_claim not in {"asserted", "proven", "rejected"}:
        agency_claim = "asserted"
    return {
        "intent_agency_organ_version": "intent_agency_organ.v1",
        "agency_note": str(prior.get("agency_note") or "")[:220],
        "active_tension_count": len(tensions),
        "active_commitment_count": len(commitments),
        "agency_claim_posture": agency_claim,
        "fixture_passed": bool(fixture.get("passed")),
        "cisiv_stage": "implementation",
        "claim_label": agency_claim,
        "read_only": True,
    }
