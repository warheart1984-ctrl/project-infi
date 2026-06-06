"""Build brain_deliberation.v1 envelopes."""

# Mythic: Brain Deliberation Validator
# Engineering: BrainDeliberationValidatorEngine
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_brain_deliberation(text: str, *, session_id: str | None = None) -> dict[str, Any]:
    return {
        "brain_deliberation_version": "brain_deliberation.v1",
        "deliberation_id": str(uuid4()),
        "emitted_at": _utc_now_iso(),
        "status": "proposal_only",
        "operator_anchor": {
            "session_id": session_id,
            "restated_intent": text[:500],
        },
        "source": {
            "layer_id": "aais.brain.nova_cortex",
            "cortex_family_id": "nova.cortex",
            "cortex_version": "1.2.0",
            "emitter": "brain_deliberation_runtime",
        },
        "stage_chain": [
            {
                "stage_kind": "options",
                "stage_id": "s1",
                "utterances": [{"utterance_id": "d1", "utterance_class": "interpretation", "text": text[:300], "artifact_refs": []}],
            },
            {
                "stage_kind": "tradeoffs",
                "stage_id": "s2",
                "utterances": [{"utterance_id": "d2", "utterance_class": "evidence_cite", "text": "Operator approval required before execution.", "artifact_refs": []}],
            },
            {
                "stage_kind": "commit",
                "stage_id": "s3",
                "utterances": [{"utterance_id": "d3", "utterance_class": "recommendation", "text": "Defer execution until operator accepts proposal.", "artifact_refs": []}],
            },
        ],
        "decision_summary": {"recommended_option": "defer", "confidence": 0.75, "rationale": "proposal_only boundary"},
        "authority_boundary": {
            "nova_may": ["stage multi-step deliberation"],
            "nova_must_not": ["self-authorize execution"],
            "jarvis_must": ["record operator decision"],
        },
        "governance": {"cisiv_stage": "implementation", "claim_label": "asserted", "replay_pointer": None},
    }
