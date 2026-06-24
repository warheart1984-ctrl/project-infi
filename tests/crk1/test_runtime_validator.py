"""CRK-1 runtime validator tests."""

from __future__ import annotations

import pytest

from src.crk1.errors import ConstitutionalError
from src.crk1.governance_receipt import issue_receipt
from src.crk1.runtime_facade import CRK1Decision, CRK1Evidence, CRK1Outcome
from src.crk1.runtime_validator import CRK1RuntimeValidator


def _validator() -> CRK1RuntimeValidator:
    return CRK1RuntimeValidator(lineage_resolver=lambda ident: [str(ident)])


def test_valid_transition_passes() -> None:
    validator = _validator()
    validator.validate(
        {
            "from_state": "ProposedDecision",
            "to_state": "ApprovedDecision",
            "decision": CRK1Decision("D1", "ID-P", ["E1"]),
            "identity": "ID-P",
            "evidence_pool": [],
            "identity_present": True,
            "evidence_present": True,
        }
    )


def test_invalid_transition_raises() -> None:
    validator = _validator()
    with pytest.raises(ConstitutionalError, match="Invalid transition"):
        validator.validate_transition("ProposedDecision", "EvidenceAdmitted", {})


def test_k0_requires_replayable_outcome() -> None:
    validator = _validator()
    with pytest.raises(ConstitutionalError, match="K0 violation"):
        validator.validate_k0(
            CRK1Decision("D1", "ID-P", ["E1"]),
            CRK1Outcome("O1", "D1", replayable=False),
            CRK1Evidence("E2", "O1", "ID-P"),
        )


def test_k1_blocks_forbidden_operation() -> None:
    validator = _validator()
    with pytest.raises(ConstitutionalError, match="K1 violation"):
        validator.validate_k1("delete(Outcome)")


def test_k2_requires_evidence() -> None:
    validator = _validator()
    with pytest.raises(ConstitutionalError, match="K2 violation"):
        validator.validate_k2(CRK1Decision("D1", "ID-P", []), "ID-P", [])


def test_k3_blocks_lineage_escape() -> None:
    validator = _validator()
    with pytest.raises(ConstitutionalError, match="K3 violation"):
        validator.validate_k3("ID-P", CRK1Evidence("E2", "O1", "ID-OTHER"))


def test_issue_receipt_on_success(crk1_runtime) -> None:
    from src.crk1.runtime_facade import CRK1Runtime

    facade = CRK1Runtime(crk1_runtime)
    identity_id = crk1_runtime.ledgers.identity.id
    decision = facade.propose_and_execute(identity=identity_id, evidence=["EVD-CRK1-001"])
    outcome = facade.get_outcomes(decision.id)[0]
    evidence = facade.replay_outcome(outcome.id)

    validator = CRK1RuntimeValidator(lineage_resolver=lambda ident: [str(ident)])
    receipt = issue_receipt(
        validator,
        {
            "from_state": "OutcomeReplayed",
            "to_state": "EvidenceAdmitted",
            "decision": decision,
            "outcome": outcome,
            "evidence": evidence,
            "identity": identity_id,
            "evidence_pool": [evidence],
            "identity_present": True,
            "evidence_present": True,
            "governance_approval": True,
            "create_outcome": True,
            "outcome_replayable": True,
            "evidence_admissible": True,
        },
    )
    assert receipt.continuity_status == "PRESERVED"
    assert receipt.k0_status == "PASS"
    assert receipt.replay_hash is not None
    assert "CRK-1 Governance Receipt" in receipt.render()
