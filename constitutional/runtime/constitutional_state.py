"""Article XV — Constitutional State Runtime (receipt-v2 bridge over constitutional_state core)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, TypeAlias

from pydantic import BaseModel, Field

from constitutional.core.graph import DOMAIN_STATE_MAPS, LEGAL_TRANSITIONS, map_domain_state, validate_transition
from constitutional.core.models import StateObject, Transition
from constitutional.runtime.receipts_v2 import (
    TransitionReceiptV2,
    is_receipt_v2_complete,
    stable_json_hash,
)

StateTransition = Transition

ConstitutionalStateName: TypeAlias = Literal[
    "Proposed",
    "Evaluated",
    "Approved",
    "Executed",
    "Observed",
    "Challenged",
    "Arbitrated",
    "Remediated",
    "Closed",
]

StateObjectType: TypeAlias = Literal[
    "ClaimState",
    "AuthorityState",
    "InstitutionState",
    "DecisionState",
    "ContinuityState",
    "SovereigntyState",
    "RealityState",
    "DomainState",
]


class ReplayResult(BaseModel):
    reconstructed_state: str
    canonical_state: str
    diverged: bool
    history_length: int
    reconstructed_version: int
    canonical_version: int
    state_id: str
    replay_hash: str


def transition_from_receipt(
    receipt: TransitionReceiptV2,
    *,
    state_object_id: str,
    accountable_party: str,
) -> Transition:
    if not is_receipt_v2_complete(receipt):
        raise ValueError(f"incomplete transition receipt: {receipt.receipt_id}")
    ts = receipt.timestamp
    try:
        timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        timestamp = datetime.now(timezone.utc)
    return Transition(
        transition_id=receipt.receipt_id,
        state_object_id=state_object_id,
        from_state=receipt.transition.from_state,
        to_state=receipt.transition.to_state,
        receipt_id=receipt.receipt_id,
        runtime=receipt.runtime,
        legal_basis=receipt.transition.legal_basis,
        accountable_party=accountable_party,
        timestamp=timestamp,
    )


def reconstruct_state(
    receipts: list[TransitionReceiptV2],
    state_obj: StateObject,
    *,
    accountable_party: str = "operator",
) -> StateObject:
    working = state_obj.model_copy(deep=True)
    for receipt in receipts:
        if receipt.transition.state_id and receipt.transition.state_id != working.state_id:
            raise ValueError(
                f"receipt {receipt.receipt_id} targets state {receipt.transition.state_id}, "
                f"expected {working.state_id}"
            )
        working.apply_transition(
            transition_from_receipt(
                receipt,
                state_object_id=working.state_id,
                accountable_party=accountable_party,
            )
        )
    return working


def reconstruct_state_at(
    receipts: list[TransitionReceiptV2],
    state_obj: StateObject,
    *,
    at_index: int,
    accountable_party: str = "operator",
) -> StateObject:
    if at_index < 0:
        raise ValueError("at_index must be >= 0")
    return reconstruct_state(receipts[: at_index + 1], state_obj, accountable_party=accountable_party)


def replay_state(
    receipts: list[TransitionReceiptV2],
    canonical_state: StateObject,
    *,
    accountable_party: str = "operator",
) -> ReplayResult:
    seed = StateObject(
        state_id=canonical_state.state_id,
        state_type=canonical_state.state_type,
        current_state="Proposed",
        invariants=list(canonical_state.invariants),
        evidence_requirements=list(canonical_state.evidence_requirements),
        authority_model=list(canonical_state.authority_model),
        reproducibility_requirements=list(canonical_state.reproducibility_requirements),
        impact_boundaries=list(canonical_state.impact_boundaries),
        accountability_chain=list(canonical_state.accountability_chain),
    )
    reconstructed = reconstruct_state(receipts, seed, accountable_party=accountable_party)
    diverged = (
        reconstructed.current_state != canonical_state.current_state
        or reconstructed.version != canonical_state.version
    )
    material = {
        "reconstructed": stable_json_hash(reconstructed.model_dump()),
        "canonical": stable_json_hash(canonical_state.model_dump()),
    }
    return ReplayResult(
        reconstructed_state=reconstructed.current_state,
        canonical_state=canonical_state.current_state,
        diverged=diverged,
        history_length=len(reconstructed.history),
        reconstructed_version=reconstructed.version,
        canonical_version=canonical_state.version,
        state_id=canonical_state.state_id,
        replay_hash=stable_json_hash(material),
    )


def parse_transition_receipts(
    payloads: list[dict | TransitionReceiptV2],
) -> list[TransitionReceiptV2]:
    out: list[TransitionReceiptV2] = []
    for item in payloads:
        if isinstance(item, TransitionReceiptV2):
            out.append(item)
        else:
            out.append(TransitionReceiptV2.model_validate(item))
    return out
