"""Build and validate brain_proposal.v1 envelopes."""

# Mythic: Brain Proposal Validator
# Engineering: BrainProposalValidatorEngine
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.brain_chain_scorer import score_chains, score_families


def _suggested_autobiographical_episodes(text: str) -> list[dict[str, Any]]:
    try:
        from src.autobiographical_agency_runtime import autobiographical_agency_runtime

        return autobiographical_agency_runtime.rank_autobiographical_candidates(text)
    except Exception:
        return []


def _suggested_social_bonds(text: str) -> list[dict[str, Any]]:
    try:
        from src.social_continuity_runtime import social_continuity_runtime

        return social_continuity_runtime.rank_social_candidates(text)
    except Exception:
        return []


def _suggested_multi_being_pacts(text: str) -> list[dict[str, Any]]:
    try:
        from src.multi_being_continuity_runtime import multi_being_continuity_runtime

        return multi_being_continuity_runtime.rank_multi_being_candidates(text)
    except Exception:
        return []


def _suggested_shared_norms(text: str) -> list[dict[str, Any]]:
    try:
        from src.culture_of_beings_runtime import culture_of_beings_runtime

        return culture_of_beings_runtime.rank_shared_norm_candidates(text)
    except Exception:
        return []


def _suggested_ecosystem_charters(text: str) -> list[dict[str, Any]]:
    try:
        from src.constitutional_ecosystem_runtime import constitutional_ecosystem_runtime

        return constitutional_ecosystem_runtime.rank_ecosystem_candidates(text)
    except Exception:
        return []


def _suggested_membrane_policies(text: str) -> list[dict[str, Any]]:
    try:
        from src.multi_organism_governance_membrane_runtime import multi_organism_governance_membrane_runtime

        return multi_organism_governance_membrane_runtime.rank_membrane_candidates(text)
    except Exception:
        return []


def _suggested_diplomatic_accords(text: str) -> list[dict[str, Any]]:
    try:
        from src.diplomacy.runtime import inter_substrate_diplomacy_runtime

        return inter_substrate_diplomacy_runtime.rank_diplomacy_candidates(text)
    except Exception:
        return []


def _suggested_norm_federation_treaties(text: str) -> list[dict[str, Any]]:
    try:
        from src.norm_federation_runtime import norm_federation_runtime

        return norm_federation_runtime.list_candidates(limit=8)
    except Exception:
        return []


def _suggested_charter_amendments(text: str) -> list[dict[str, Any]]:
    try:
        from src.constitutional_evolution_runtime import constitutional_evolution_runtime

        return constitutional_evolution_runtime.list_candidates(limit=8)
    except Exception:
        return []


def _suggested_civilization_charters(text: str) -> list[dict[str, Any]]:
    try:
        from src.governed_civilization_runtime import governed_civilization_runtime

        return governed_civilization_runtime.list_candidates(limit=8)
    except Exception:
        return []


def _suggested_narrative_beats(text: str) -> list[dict[str, Any]]:
    try:
        from src.narrative_continuity_runtime import narrative_continuity_runtime

        return narrative_continuity_runtime.rank_narrative_candidates(text)
    except Exception:
        return []


def _suggested_identity_claims(text: str) -> list[dict[str, Any]]:
    try:
        from src.identity_self_model_runtime import identity_self_model_runtime

        return identity_self_model_runtime.rank_identity_candidates(text)
    except Exception:
        return []


def _suggested_habits(text: str) -> list[dict[str, Any]]:
    try:
        from src.culture_habit_runtime import culture_habit_runtime

        return culture_habit_runtime.rank_habit_candidates(text)
    except Exception:
        return []


def _suggested_organ_mesh(text: str) -> dict[str, Any] | None:
    try:
        from src.organ_coordination_runtime import organ_coordination_runtime

        plan = organ_coordination_runtime.plan_mesh_run(intent_text=text)
        if plan.get("outcome") != "planned":
            return None
        return {
            "plan_id": plan.get("plan_id"),
            "edge": plan.get("edge"),
            "steps": plan.get("steps"),
            "occ_class": plan.get("occ_class"),
        }
    except Exception:
        return None

FORBIDDEN_KEYS = frozenset({"execute", "authorized", "approved", "tool_call", "shell_command"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_brain_proposal(text: str, *, emitter: str = "brain_layer_runtime") -> dict[str, Any]:
    families = score_families(text)
    chains = score_chains(text)
    top_family = families[0] if families else {}
    top_chain = chains[0] if chains else {}
    suggested_mesh = _suggested_organ_mesh(text)
    suggested_habits = _suggested_habits(text)
    suggested_identity = _suggested_identity_claims(text)
    suggested_narrative = _suggested_narrative_beats(text)
    suggested_autobiographical = _suggested_autobiographical_episodes(text)
    suggested_social = _suggested_social_bonds(text)
    suggested_multi_being = _suggested_multi_being_pacts(text)
    suggested_shared_norms = _suggested_shared_norms(text)
    suggested_ecosystem_charters = _suggested_ecosystem_charters(text)
    suggested_membrane_policies = _suggested_membrane_policies(text)
    suggested_diplomatic_accords = _suggested_diplomatic_accords(text)
    suggested_norm_federation_treaties = _suggested_norm_federation_treaties(text)
    suggested_charter_amendments = _suggested_charter_amendments(text)
    suggested_civilization_charters = _suggested_civilization_charters(text)
    return {
        "brain_proposal_version": "brain_proposal.v1",
        "proposal_id": str(uuid4()),
        "emitted_at": _utc_now_iso(),
        "status": "proposal_only",
        "proposal_kind": "routing_recommendation",
        "source": {
            "layer_id": "aais.brain.nova_cortex",
            "cortex_family_id": "nova.cortex",
            "cortex_version": "1.2.0",
            "emitter": emitter,
        },
        "intent": {
            "restated_task": text[:500],
            "frame_kind": "companion",
            "confidence": 0.8,
        },
        "utterances": [
            {
                "utterance_id": "u1",
                "utterance_class": "interpretation",
                "text": f"Top candidate: {top_chain.get('workflow_id', 'none')} under {top_family.get('family_id', 'unknown')}.",
                "artifact_refs": [],
                "max_chars": 512,
            }
        ],
        "routing": {
            "organ_rankings": families[:4],
            "chain_rankings": chains[:4],
            "suggested_workflow_chain": top_chain or None,
            "suggested_organ_mesh": suggested_mesh,
            "suggested_habits": suggested_habits,
            "suggested_identity_claims": suggested_identity,
            "suggested_narrative_beats": suggested_narrative,
            "suggested_autobiographical_episodes": suggested_autobiographical,
            "suggested_social_bonds": suggested_social,
            "suggested_multi_being_pacts": suggested_multi_being,
            "suggested_shared_norms": suggested_shared_norms,
            "suggested_ecosystem_charters": suggested_ecosystem_charters,
            "suggested_membrane_policies": suggested_membrane_policies,
            "suggested_diplomatic_accords": suggested_diplomatic_accords,
            "suggested_norm_federation_treaties": suggested_norm_federation_treaties,
            "suggested_charter_amendments": suggested_charter_amendments,
            "suggested_civilization_charters": suggested_civilization_charters,
        },
        "authority_boundary": {
            "nova_may": ["interpret operator intent", "recommend workflow-family routing"],
            "nova_must_not": ["self-authorize tool execution", "emit ActionType fields"],
            "jarvis_must": ["authorize tool/action paths", "enforce policy gates"],
        },
        "governance": {
            "cisiv_stage": "implementation",
            "claim_label": "asserted",
            "replay_pointer": None,
        },
    }


def validate_brain_proposal(proposal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if proposal.get("status") != "proposal_only":
        errors.append("status must be proposal_only")
    if proposal.get("brain_proposal_version") != "brain_proposal.v1":
        errors.append("invalid brain_proposal_version")
    blob = str(proposal)
    for key in FORBIDDEN_KEYS:
        if f'"{key}"' in blob and key in proposal:
            errors.append(f"forbidden key {key}")
    return errors
