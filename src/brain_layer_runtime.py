"""Nova Cortex bounded brain-layer runtime."""

# Mythic: Brain Layer
# Engineering: BrainLayerRuntimeEngine
from __future__ import annotations

from typing import Any

from src.brain_deliberation_runtime import deliberate
from src.brain_proposal_validator import build_brain_proposal, validate_brain_proposal
from src.brain_session_store import brain_session_store

MODULE_ID = "AAIS-BLR-01"


def build_brain_status() -> dict[str, Any]:
    sessions = brain_session_store.list_sessions()
    return {
        "module_id": MODULE_ID,
        "layer_id": "aais.brain.nova_cortex",
        "status": "proposal_only",
        "session_count": len(sessions),
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }


def propose(text: str) -> dict[str, Any]:
    proposal = build_brain_proposal(text)
    errors = validate_brain_proposal(proposal)
    if errors:
        return {"ok": False, "errors": errors}
    return {"ok": True, "proposal": proposal}


def deliberate_text(text: str, *, session_id: str | None = None) -> dict[str, Any]:
    return {"ok": True, "deliberation": deliberate(text, session_id=session_id)}
