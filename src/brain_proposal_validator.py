"""Build and validate brain_proposal.v1 envelopes."""

# Mythic: Brain Proposal Validator
# Engineering: BrainProposalValidatorEngine
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.brain_chain_scorer import score_chains, score_families

FORBIDDEN_KEYS = frozenset({"execute", "authorized", "approved", "tool_call", "shell_command"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_brain_proposal(text: str, *, emitter: str = "brain_layer_runtime") -> dict[str, Any]:
    families = score_families(text)
    chains = score_chains(text)
    top_family = families[0] if families else {}
    top_chain = chains[0] if chains else {}
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
