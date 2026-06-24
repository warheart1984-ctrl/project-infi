"""CRK-1 §2 — Core object model property tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.continuity.constitutional_runtime import DEFAULT_IDENTITY, IdentityObject
from src.continuity.decision_ledger import DecisionLedgerStore, bootstrap_decision_ledger
from src.continuity.outcome_ledger import OutcomeLedgerStore, bootstrap_outcome_ledger

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "fixtures" / "continuity"


@pytest.mark.parametrize(
    "schema_file",
    [
        "decision_record.schema.json",
        "outcome_record.schema.json",
        "resource_record.schema.json",
        "identity_record.schema.json",
        "evidence_record.schema.json",
    ],
)
def test_crk1_object_schema_frozen(schema_file: str) -> None:
    """Kernel object schemas exist and declare required fields."""
    path = SCHEMA_DIR / schema_file
    assert path.is_file(), f"missing schema {schema_file}"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload.get("title")
    assert payload.get("required")


def test_identity_object_invariants_present() -> None:
    """IdentityObject carries non-empty invariants (CRK-1.2)."""
    identity = DEFAULT_IDENTITY
    assert isinstance(identity, IdentityObject)
    assert identity.id
    assert identity.mission
    assert len(identity.values) >= 1
    assert len(identity.invariants) >= 1
    assert identity.authority_model


def test_decision_object_references_identity(crk1_ledgers) -> None:
    store = crk1_ledgers.decisions
    bootstrap_decision_ledger(store, epoch=17)
    record = store.get("DEC-2026-0001")
    assert record is not None
    assert record.identity_id == DEFAULT_IDENTITY.id


def test_outcome_object_references_decision(crk1_ledgers) -> None:
    store = crk1_ledgers.outcomes
    bootstrap_outcome_ledger(store, epoch=17)
    outcomes = store.list_outcomes()
    assert outcomes
    for outcome in outcomes:
        assert outcome.decision_id
        assert outcome.expected is not None
        assert outcome.observed is not None
        assert outcome.variance is not None


def test_outcome_expected_observed_immutable_after_record(crk1_ledgers) -> None:
    """Recorded outcomes preserve expected/observed (CRK-1 object test B)."""
    store = crk1_ledgers.outcomes
    bootstrap_outcome_ledger(store, epoch=17)
    first = store.list_outcomes()[0]
    expected_snapshot = dict(first.expected)
    observed_snapshot = dict(first.observed)
    reloaded = store.get(first.id)
    assert reloaded is not None
    assert reloaded.expected == expected_snapshot
    assert reloaded.observed == observed_snapshot
