from __future__ import annotations

from typing import Any

from nova.crk.identity.identity_history import append_ratified_amendment
from nova.governance.steward_ledger import get_steward_ledger
from nova.governance.steward_models import (
    AmendmentProposal,
    RatifiedAmendment,
    StewardId,
    StewardSignature,
)
from nova.law_kernel import t5_binding


def propose_amendment(steward_id: str, payload: dict[str, Any]) -> AmendmentProposal:
    ledger = get_steward_ledger()
    ref = t5_binding.T5ReferenceSignal.current()
    proposal = AmendmentProposal(
        id=f"amend-proposal:{len(ledger.list_proposals())}",
        steward_id=StewardId(steward_id),
        payload=dict(payload),
        lineage_event_id=f"le:proposal:{steward_id}:{len(ledger.list_proposals())}",
    )
    ledger.record_proposal(proposal)
    return proposal


def ratify_amendment(steward_id: str, proposal_id: str) -> RatifiedAmendment:
    ledger = get_steward_ledger()
    proposal = ledger.get_proposal(proposal_id)
    if proposal is None:
        raise KeyError(f"Unknown proposal: {proposal_id}")

    ref = t5_binding.T5ReferenceSignal.current()
    signature = StewardSignature(
        steward_id=StewardId(steward_id),
        signed_at=proposal.created_at,
        t5_ref_signal_hash=ref.hash,
        lineage_event_id=f"le:ratify:{proposal_id}:{steward_id}",
    )
    amendment = RatifiedAmendment(
        proposal_id=proposal_id,
        signatures=[signature],
        payload=dict(proposal.payload),
        lineage_event_id=f"le:amendment:{proposal_id}",
        t5_ref_signal_hash=ref.hash,
    )
    ledger.record_ratification(amendment)
    append_ratified_amendment(amendment)
    return amendment
