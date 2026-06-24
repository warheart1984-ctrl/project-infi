"""CRK-1 governance engine and consequence preservation tests."""

from __future__ import annotations

import pytest

from src.crk1.errors import ConstitutionalError
from src.crk1.governance_engine import GovernanceEngine
from src.crk1.integrity_monitor import IntegrityMonitor
from src.crk1.runtime_facade import CRK1Runtime
from src.crk1.runtime_validator import CRK1RuntimeValidator


def test_governance_propose_ratify(crk1_runtime) -> None:
    facade = CRK1Runtime(crk1_runtime)
    engine = GovernanceEngine(facade, CRK1RuntimeValidator())
    root = crk1_runtime.ledgers.identity.id

    decision = engine.propose(
        root,
        {
            "type": "policy",
            "content": {"rule": "test"},
            "justification": "unit test",
            "evidence_ids": ["EVD-CRK1-001"],
        },
    )
    outcome, evidence = engine.ratify(decision.id)
    assert outcome.replayable is True
    assert evidence.admissible_for_decision is True


def test_amendment_rejected_when_insulating(crk1_runtime) -> None:
    facade = CRK1Runtime(crk1_runtime)
    engine = GovernanceEngine(facade, CRK1RuntimeValidator())
    root = crk1_runtime.ledgers.identity.id

    with pytest.raises(ConstitutionalError, match="K5 violation"):
        engine.amend(
            root,
            {
                "changes": {"Outcome.replayable": False},
                "evidence_ids": ["EVD-CRK1-001"],
                "justification": "bad amendment",
            },
        )


def test_amendment_allowed_when_preserving_consequences(crk1_runtime) -> None:
    facade = CRK1Runtime(crk1_runtime)
    engine = GovernanceEngine(facade, CRK1RuntimeValidator())
    root = crk1_runtime.ledgers.identity.id

    outcome, evidence = engine.amend(
        root,
        {
            "changes": {"governance.quorum": 3},
            "evidence_ids": ["EVD-CRK1-001"],
            "justification": "raise quorum",
        },
    )
    assert outcome.replayable is True
    assert evidence.admissible_for_decision is True


def test_integrity_monitor_full_scan(crk1_runtime) -> None:
    facade = CRK1Runtime(crk1_runtime)
    validator = CRK1RuntimeValidator()
    monitor = IntegrityMonitor(facade, validator)
    root = crk1_runtime.ledgers.identity.id

    facade.propose_and_execute(identity=root, evidence=["EVD-CRK1-001"])
    assert monitor.check_continuity() is True
