"""CRK-1 commit-refusing governance gate tests."""

from __future__ import annotations

import pytest

from src.crk1.crk1_governance_engine import CRK1GovernanceEngine
from src.crk1.errors import ConstitutionalError
from src.crk1.governance_receipt_header import build_governance_receipt_header
from src.crk1.governance_receipt_merkleizer import merkle_root
from src.crk1.runtime_facade import CRK1Runtime
from src.crk1.runtime_validator import CRK1RuntimeValidator


def _sample_receipt(runtime) -> dict:
    identity_id = runtime.kernel.ledgers.identity.id
    evidence = runtime.create_evidence()
    header = build_governance_receipt_header(
        runtime,
        action_type="certification",
        actor_identity=identity_id,
        context={"transition_ok": True, "se_before": 1.0, "se_after": 1.0},
        decision_summary="gate test",
        evidence_refs=[evidence.id],
        include_redteam=False,
    )
    return header.to_dict()


def test_commit_action_verifies_anchors_then_applies(runtime) -> None:
    applied: list[dict] = []

    def apply_fn(action: dict) -> None:
        applied.append(action)

    gate = CRK1GovernanceEngine(apply_fn)
    receipt = _sample_receipt(runtime)
    gate.commit_action({"kind": "certification"}, receipt, require_redteam=False)

    assert applied == [{"kind": "certification"}]
    assert len(gate.receipts) == 1
    assert gate.merkle_root == merkle_root(gate.receipts)
    assert gate.index.get_by_id(receipt["receipt_id"]) is receipt


def test_commit_refuses_without_receipt(runtime) -> None:
    gate = CRK1GovernanceEngine(lambda _action: None)
    with pytest.raises(ConstitutionalError, match="receipt required"):
        gate.commit_action({"kind": "mutation"}, {})


def test_commit_refuses_invalid_receipt(runtime) -> None:
    applied = False

    def apply_fn(_action: dict) -> None:
        nonlocal applied
        applied = True

    gate = CRK1GovernanceEngine(apply_fn)
    receipt = _sample_receipt(runtime)
    receipt["invariants_checked"]["K0_K2"] = "FAIL"

    with pytest.raises(ConstitutionalError, match="K0"):
        gate.commit_action({"kind": "mutation"}, receipt, require_redteam=False)

    assert applied is False
    assert gate.receipts == []
    assert gate.merkle_root == merkle_root([])


def test_merkle_root_updates_across_commits(runtime) -> None:
    gate = CRK1GovernanceEngine(lambda _action: None)
    root_empty = gate.merkle_root

    gate.commit_action({"n": 1}, _sample_receipt(runtime), require_redteam=False)
    root_one = gate.merkle_root

    gate.commit_action({"n": 2}, _sample_receipt(runtime), require_redteam=False)
    root_two = gate.merkle_root

    assert root_empty != root_one
    assert root_one != root_two


def test_governance_engine_uses_commit_gate(crk1_runtime) -> None:
    facade = CRK1Runtime(crk1_runtime)
    from src.crk1.governance_engine import GovernanceEngine

    engine = GovernanceEngine(facade, CRK1RuntimeValidator())
    root = crk1_runtime.ledgers.identity.id
    root_before = engine.merkle_root

    engine.amend(
        root,
        {
            "changes": {"governance.quorum": 3},
            "evidence_ids": ["EVD-CRK1-001"],
            "justification": "raise quorum",
        },
    )

    assert engine.merkle_root != root_before
    assert len(engine.commit_gate.receipts) == 1
    assert engine.audit_failures() == []
