"""Tests for CRK-1 runtime assertion guards."""

from __future__ import annotations

import pytest

from src.crk1.errors import ConstitutionalError
from src.crk1.runtime_assertions import (
    assert_decision_has_evidence,
    assert_decision_has_identity,
    assert_evidence_admissible,
    assert_execution_produces_outcome,
    assert_lineage_inherits_evidence,
    assert_no_evidence_quarantine,
    assert_no_outcome_deletion,
    assert_outcome_replayable,
    assert_replay_produces_evidence,
)
from src.crk1.runtime_facade import CRK1Decision, CRK1Evidence, CRK1Outcome


def test_assert_outcome_replayable_passes() -> None:
    assert_outcome_replayable(CRK1Outcome("O1", "D1", replayable=True))


def test_assert_outcome_replayable_fails() -> None:
    with pytest.raises(ConstitutionalError, match="K1 violation"):
        assert_outcome_replayable(CRK1Outcome("O1", "D1", replayable=False))


def test_assert_evidence_admissible_fails() -> None:
    with pytest.raises(ConstitutionalError, match="K1 violation"):
        assert_evidence_admissible(
            CRK1Evidence("E1", "O1", "ID-P", admissible_for_decision=False)
        )


def test_assert_decision_requires_evidence() -> None:
    with pytest.raises(ConstitutionalError, match="K2 violation"):
        assert_decision_has_evidence(CRK1Decision("D1", "ID-P", []))


def test_assert_decision_requires_identity() -> None:
    class _Decision:
        input_evidence_ids = ["E1"]
        identity_id = None

    with pytest.raises(ConstitutionalError, match="K2 violation"):
        assert_decision_has_identity(_Decision())


def test_assert_lineage_inherits_evidence() -> None:
    evidence = CRK1Evidence("E1", "O1", "ID-ANCESTOR")
    with pytest.raises(ConstitutionalError, match="K3 violation"):
        assert_lineage_inherits_evidence(
            "ID-CHILD",
            evidence,
            lambda ident: [str(ident)],
        )


def test_assert_forbidden_operations_raise() -> None:
    with pytest.raises(ConstitutionalError, match="Outcome deletion"):
        assert_no_outcome_deletion()
    with pytest.raises(ConstitutionalError, match="quarantine"):
        assert_no_evidence_quarantine()


def test_assert_replay_produces_evidence() -> None:
    with pytest.raises(ConstitutionalError, match="K0 violation"):
        assert_replay_produces_evidence(None)


def test_assert_execution_produces_outcome() -> None:
    with pytest.raises(ConstitutionalError, match="K0 violation"):
        assert_execution_produces_outcome(None)
