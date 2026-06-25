"""Identity history ledger and evaluator tests."""

from __future__ import annotations

from src.continuity.decision_ledger import DecisionLedgerStore, DecisionRecord, bootstrap_decision_ledger
from src.continuity.identity_object import DEFAULT_IDENTITY, IdentityObject
from src.kernel.identity_history import IdentityHistory, IdentityIntegrityEvaluator, IdentitySnapshot
from src.kernel.identity_history_ledger import reset_identity_ledger, shared_identity_ledger


def test_identity_history_loads_ledger_snapshots() -> None:
    reset_identity_ledger()
    shared_identity_ledger().append(
        identity=DEFAULT_IDENTITY, epoch=10, kernel_version=1, reason="epoch-10"
    )
    history = IdentityHistory(
        [
            IdentitySnapshot(epoch=0, identity=DEFAULT_IDENTITY),
            IdentitySnapshot(
                epoch=10,
                identity=IdentityObject.from_dict(shared_identity_ledger().list()[0].identity),
            ),
        ]
    )
    assert history.active_identity.id == DEFAULT_IDENTITY.id
    assert len(history.snapshots) == 2


def test_invariant_erosion_counts_governance_exceptions() -> None:
    store = DecisionLedgerStore.in_memory()
    bootstrap_decision_ledger(store, epoch=17)
    store.upsert(
        DecisionRecord.from_dict(
            {
                "id": "DEC-INV-EX-01",
                "actor_id": "ROLE-STEWARD-01",
                "identity_id": "CIV-CORE-01",
                "intent": "Emergency bypass",
                "type": "operational",
                "evidence_refs": ["EV-1"],
                "risk_profile": {},
                "governance_basis": {"invariant_exception": True},
                "resource_plan": {},
                "status": "proposed",
                "epoch": 17,
                "tags": [],
                "notes": "",
                "created_at": "2026-06-21T00:00:00Z",
                "updated_at": "2026-06-21T00:00:00Z",
            }
        )
    )
    history = IdentityHistory.from_identity(DEFAULT_IDENTITY, epoch=17)
    evaluator = IdentityIntegrityEvaluator(history, decisions=store)
    assert evaluator.invariant_erosion_score() > 0.0
