"""CRK-1 governance receipt header schema and validation tests."""

from __future__ import annotations

import uuid

import pytest

from src.crk1.consequence_lattice import ConsequenceExposure
from src.crk1.errors import ConstitutionalError
from src.crk1.governance_engine import GovernanceEngine
from src.crk1.governance_receipt_header import (
    RUNTIME_VERSION,
    build_governance_receipt_header,
    compute_kernel_state_hash,
    compute_ledger_state_hash,
    crk1_uuid,
    validate_governance_receipt_header,
)
from src.crk1.runtime_facade import CRK1Runtime
from src.crk1.runtime_validator import CRK1RuntimeValidator
from src.crk1.schema_validator import CRK1SchemaValidator

def test_schema_validates_header(runtime) -> None:
    identity_id = runtime.kernel.ledgers.identity.id
    evidence = runtime.create_evidence()
    header = build_governance_receipt_header(
        runtime,
        action_type="certification",
        actor_identity=identity_id,
        context={"transition_ok": True, "se_before": 1.0, "se_after": 1.0},
        decision_summary="certify continuity substrate",
        evidence_refs=[evidence.id],
        include_redteam=False,
    )
    CRK1SchemaValidator().validate("GovernanceReceiptHeader", header.to_dict())
    validate_governance_receipt_header(header)


def test_crk1_uuid_maps_non_uuid_ids() -> None:
    mapped = crk1_uuid("CIV-CORE-01")
    uuid.UUID(mapped)
    assert mapped == crk1_uuid("CIV-CORE-01")


def test_state_hashes_are_sha256(runtime) -> None:
    kernel_hash = compute_kernel_state_hash(runtime)
    ledger_hash = compute_ledger_state_hash(runtime)
    assert len(kernel_hash) == 64
    assert len(ledger_hash) == 64
    assert kernel_hash.isupper()


def test_rejects_ce_regression(runtime) -> None:
    identity_id = runtime.kernel.ledgers.identity.id
    evidence = runtime.create_evidence()
    header = build_governance_receipt_header(
        runtime,
        action_type="mutation",
        actor_identity=identity_id,
        context={
            "transition_ok": True,
            "ce_before": ConsequenceExposure(0.9, 1.0, 1.0, 1.0, 1.0, 1.0),
            "ce_after": ConsequenceExposure(0.5, 1.0, 1.0, 1.0, 1.0, 1.0),
            "se_before": 1.0,
            "se_after": 1.0,
        },
        decision_summary="bad drift",
        evidence_refs=[evidence.id],
        include_redteam=False,
    )
    with pytest.raises(ConstitutionalError, match="K3"):
        validate_governance_receipt_header(header)


def test_governance_engine_issues_header_on_amend(crk1_runtime) -> None:
    facade = CRK1Runtime(crk1_runtime)
    engine = GovernanceEngine(facade, CRK1RuntimeValidator())
    root = crk1_runtime.ledgers.identity.id

    engine.amend(
        root,
        {
            "changes": {"governance.quorum": 3},
            "evidence_ids": ["EVD-CRK1-001"],
            "justification": "raise quorum",
        },
    )
    header = engine.last_receipt_header
    assert header is not None
    assert header.runtime_version == RUNTIME_VERSION
    assert header.action_type == "mutation"
    assert header.invariants_checked["K0_K2"] == "PASS"
    assert header.redteam_status["all_blocked"] == "YES"
    validate_governance_receipt_header(header)
