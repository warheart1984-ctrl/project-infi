"""CSR bridge — register domain state documents as constitutional StateObjects."""

from __future__ import annotations

from typing import Protocol

from constitutional.core.models import StateObject
from constitutional.runtime.domain_invariants import ALL_DOMAIN_INVARIANTS
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from pydantic import BaseModel


class DomainStateDoc(Protocol):
    state_type: str


def state_id_from_doc(doc: BaseModel) -> str:
    fields = type(doc).model_fields
    for key in (
        "state_id",
        "idea_id",
        "assumption_id",
        "lineage_id",
        "context_id",
        "person_id",
        "relationship_id",
        "interaction_id",
        "commitment_id",
        "signal_id",
        "insight_id",
        "question_id",
        "hypothesis_id",
        "model_id",
        "pattern_id",
        "role_id",
        "snapshot_id",
        "priority_id",
        "opportunity_id",
        "dependency_id",
        "portfolio_id",
        "asset_id",
        "statement_id",
        "reference_id",
        "profile_id",
        "plan_id",
        "source_id",
    ):
        if key in fields and hasattr(doc, key):
            value = getattr(doc, key, None)
            if value is not None:
                return str(value)
    raise ValueError(f"cannot derive state_id from {type(doc).__name__}")


def register_domain_state(
    csr: ConstitutionalStateRuntime,
    doc: BaseModel,
    *,
    runtime_key: str,
    initial_constitutional_state: str = "Proposed",
) -> StateObject:
    """Register a domain document as a governed StateObject."""
    state_type = str(getattr(doc, "state_type", doc.__class__.__name__))
    state_id = state_id_from_doc(doc)
    invariants = sorted(ALL_DOMAIN_INVARIANTS.get(runtime_key, frozenset()))
    state = StateObject(
        state_id=state_id,
        state_type=state_type,
        current_state=initial_constitutional_state,
        invariants=invariants,
        evidence_requirements=[f"{state_type}:evidence"],
        authority_model=["founder", "runtime_law_spine"],
        reproducibility_requirements=["exact"],
        impact_boundaries=[runtime_key],
        accountability_chain=["founder"],
    )
    csr.register_state(state)
    if isinstance(doc, BaseModel):
        csr.put_domain_doc(state_id, state_type, doc)
    return state
