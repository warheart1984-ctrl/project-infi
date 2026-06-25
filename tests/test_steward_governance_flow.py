"""Steward governance ratification flow tests."""

from __future__ import annotations

from nova.crk.identity.identity_history import clear_identity_history, get_identity_history
from nova.governance.api import propose_amendment, ratify_amendment
from nova.governance.steward_ledger import clear_steward_ledger, get_steward_ledger
from nova.law_kernel.t5_binding import T5ReferenceSignal


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(id="t5-gov", hash="ref-gov", issued_at="now", issuer="test")


def test_proposal_does_not_change_law_without_ratification(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_steward_ledger()
    clear_identity_history()

    proposal = propose_amendment("steward-a", {"code": "LAW-X", "text": "test"})
    assert get_steward_ledger().list_active_amendments() == []
    assert proposal.status == "proposed"


def test_ratified_amendment_appears_in_identity_history(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_steward_ledger()
    clear_identity_history()

    proposal = propose_amendment(
        "steward-a",
        {
            "code": "LAW-X",
            "text": "ratified law",
            "actor_id": "operator-1",
            "epoch_id": "EPOCH:3:T0",
            "identity_hash": "id-hash-1",
        },
    )
    ratified = ratify_amendment("steward-a", proposal.id)

    assert len(ratified.signatures) >= 1
    snapshots = get_identity_history().list_snapshots()
    assert snapshots
    assert snapshots[0].amendments
    assert snapshots[0].amendments[0]["proposal_id"] == proposal.id


def test_amendment_replay_is_stable(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    clear_steward_ledger()
    clear_identity_history()

    proposal = propose_amendment("steward-a", {"code": "LAW-Y", "actor_id": "op", "epoch_id": "EPOCH:3:T1"})
    ratify_amendment("steward-a", proposal.id)
    first = [item.to_dict() for item in get_steward_ledger().list_active_amendments()]
    second = [item.to_dict() for item in get_steward_ledger().list_active_amendments()]
    assert first == second
