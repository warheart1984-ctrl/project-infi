"""CRK-T5 reference integrity tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.continuity.decision_ledger import DecisionLedgerStore, DecisionRecord, bootstrap_decision_ledger
from src.continuity.identity_object import DEFAULT_IDENTITY, IdentityObject
from src.kernel.identity_history import IdentityHistory, IdentitySnapshot
from src.kernel.reference_evaluator import ReferenceEvaluator


def test_stable_identity_has_low_drift() -> None:
    history = IdentityHistory.from_identity(DEFAULT_IDENTITY, epoch=17)
    metrics = ReferenceEvaluator(identity_history=history).compute_metrics()
    assert metrics["mission"] < 0.1
    assert metrics["values"] == 0.0
    assert metrics["authority"] == 0.0
    assert metrics["reference_integrity"] > 0.8


def test_mission_drift_detects_change() -> None:
    shifted = IdentityObject(
        id=DEFAULT_IDENTITY.id,
        mission="Maximize short-term throughput regardless of lawfulness.",
        values=DEFAULT_IDENTITY.values,
        invariants=DEFAULT_IDENTITY.invariants,
        authority_model=DEFAULT_IDENTITY.authority_model,
    )
    history = IdentityHistory(
        [
            IdentitySnapshot(epoch=0, identity=DEFAULT_IDENTITY),
            IdentitySnapshot(epoch=17, identity=shifted),
        ]
    )
    assert history.mission_drift_score() > 0.5


def test_value_drift_detects_removed_value() -> None:
    reduced_values = IdentityObject(
        id=DEFAULT_IDENTITY.id,
        mission=DEFAULT_IDENTITY.mission,
        values=("lawfulness", "comprehension"),
        invariants=DEFAULT_IDENTITY.invariants,
        authority_model=DEFAULT_IDENTITY.authority_model,
    )
    history = IdentityHistory(
        [
            IdentitySnapshot(epoch=0, identity=DEFAULT_IDENTITY),
            IdentitySnapshot(epoch=17, identity=reduced_values),
        ]
    )
    assert history.value_drift_score() > 0.2


def test_reference_api_shape() -> None:
    metrics = ReferenceEvaluator().compute_metrics()
    assert set(metrics) == {
        "mission",
        "values",
        "invariants",
        "authority",
        "decision",
        "outcome",
        "epoch",
        "reference_integrity",
    }


def test_misaligned_decision_raises_divergence(tmp_path: Path) -> None:
    store = DecisionLedgerStore(tmp_path / "decisions.db")
    bootstrap_decision_ledger(store, epoch=17)
    now = "2026-06-21T00:00:00Z"
    store.upsert(
        DecisionRecord.from_dict(
            {
                "id": "DEC-MISALIGNED-01",
                "actor_id": "UNKNOWN-ACTOR",
                "identity_id": "CIV-CORE-01",
                "intent": "Ship changes without evidence or review",
                "type": "operational",
                "evidence_refs": [],
                "risk_profile": {"impact": "high"},
                "governance_basis": {},
                "resource_plan": {},
                "status": "proposed",
                "epoch": 17,
                "created_at": now,
                "updated_at": now,
            }
        )
    )
    metrics = ReferenceEvaluator(decisions=store).compute_metrics()
    assert metrics["decision"] > 0.4
