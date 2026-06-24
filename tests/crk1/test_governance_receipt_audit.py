"""CRK-1 governance receipt verifier, merkleizer, and index tests."""

from __future__ import annotations

import pytest

from src.crk1.errors import ConstitutionalError
from src.crk1.governance_engine import GovernanceEngine
from src.crk1.governance_receipt_header import build_governance_receipt_header
from src.crk1.governance_receipt_index import GovernanceReceiptIndex
from src.crk1.governance_receipt_merkleizer import audit_spine, hash_receipt, merkle_root
from src.crk1.governance_receipt_verifier import GovernanceReceiptVerifier
from src.crk1.runtime_facade import CRK1Runtime
from src.crk1.runtime_validator import CRK1RuntimeValidator


def _sample_receipt(runtime, **context_overrides):
    identity_id = runtime.kernel.ledgers.identity.id
    evidence = runtime.create_evidence()
    context = {
        "transition_ok": True,
        "se_before": 1.0,
        "se_after": 1.0,
        **context_overrides,
    }
    header = build_governance_receipt_header(
        runtime,
        action_type="certification",
        actor_identity=identity_id,
        context=context,
        decision_summary="audit test",
        evidence_refs=[evidence.id],
        include_redteam=False,
    )
    return header.to_dict()


def test_verifier_accepts_valid_receipt(runtime) -> None:
    receipt = _sample_receipt(runtime)
    assert GovernanceReceiptVerifier().verify(receipt, require_redteam=False) is True


def test_verifier_rejects_invariant_failure(runtime) -> None:
    receipt = _sample_receipt(runtime)
    receipt["invariants_checked"]["K3_K6"] = "FAIL"
    with pytest.raises(ConstitutionalError, match="K3"):
        GovernanceReceiptVerifier().verify(receipt, require_redteam=False)


def test_verifier_rejects_ce_drift(runtime) -> None:
    receipt = _sample_receipt(runtime)
    receipt["drift_metrics"]["CE_before"] = 0.9
    receipt["drift_metrics"]["CE_after"] = 0.5
    with pytest.raises(ConstitutionalError, match="CE"):
        GovernanceReceiptVerifier().verify(receipt, require_redteam=False)


def test_verifier_rejects_redteam_not_blocked(runtime) -> None:
    receipt = _sample_receipt(runtime)
    receipt["redteam_status"]["all_blocked"] = "NO"
    with pytest.raises(ConstitutionalError, match="Red"):
        GovernanceReceiptVerifier().verify(receipt)


def test_merkle_root_is_stable(runtime) -> None:
    receipts = [_sample_receipt(runtime), _sample_receipt(runtime)]
    root_a = merkle_root(receipts)
    root_b = merkle_root(receipts)
    assert root_a == root_b
    assert len(root_a) == 64


def test_merkle_root_empty() -> None:
    assert len(merkle_root([])) == 64


def test_hash_receipt_canonical(runtime) -> None:
    receipt = _sample_receipt(runtime)
    reordered = dict(sorted(receipt.items(), key=lambda item: item[0]))
    assert hash_receipt(receipt) == hash_receipt(reordered)


def test_index_queries_and_failures(runtime) -> None:
    index = GovernanceReceiptIndex()
    good = _sample_receipt(runtime)
    bad = _sample_receipt(runtime)
    bad["invariants_checked"]["K7_K12"] = "FAIL"

    index.add_receipt(good)
    index.add_receipt(bad)

    assert index.get_by_id(good["receipt_id"]) is good
    assert len(index.get_by_actor(good["actor_identity"])) == 2
    assert len(index.get_by_action_type("certification")) == 2
    failures = index.find_failures()
    assert len(failures) == 1
    assert failures[0]["receipt_id"] == bad["receipt_id"]


def test_index_merkle_spine(runtime) -> None:
    index = GovernanceReceiptIndex()
    index.add_receipt(_sample_receipt(runtime))
    index.add_receipt(_sample_receipt(runtime))
    spine = index.audit_spine()
    assert spine["receipt_count"] == 2
    assert spine["merkle_root"] == index.merkle_root()
    assert len(spine["leaf_hashes"]) == 2
    assert audit_spine(index.all_receipts()) == spine


def test_governance_engine_populates_index(crk1_runtime) -> None:
    facade = CRK1Runtime(crk1_runtime)
    index = GovernanceReceiptIndex()
    engine = GovernanceEngine(
        facade,
        CRK1RuntimeValidator(),
        receipt_index=index,
    )
    root = crk1_runtime.ledgers.identity.id

    engine.amend(
        root,
        {
            "changes": {"governance.quorum": 3},
            "evidence_ids": ["EVD-CRK1-001"],
            "justification": "raise quorum",
        },
    )

    assert engine.last_receipt_header is not None
    assert len(index.all_receipts()) == 1
    assert index.merkle_root() == merkle_root(index.all_receipts())
    assert index.find_failures() == []
