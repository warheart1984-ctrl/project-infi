"""CRK-1 §3 — Contract property tests (evidence, governance, resource)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.continuity.constitutional_runtime import (
    DEFAULT_IDENTITY,
    EvidenceContract,
    GovernanceContract,
)
from src.continuity.decision_ledger import DecisionLedgerStore, DecisionRecord, DecisionStatus
from src.continuity.resource_contract import ResourceContract
from src.continuity.resource_ledger import (
    ResourceLedgerStore,
    ResourceObject,
    ResourceStatus,
    ResourceType,
)


def _time_resource(
    resource_id: str,
    *,
    total: float,
    allocated: float = 0.0,
    status: ResourceStatus = ResourceStatus.ACTIVE,
) -> ResourceObject:
    return ResourceObject(
        id=resource_id,
        type=ResourceType.TIME.value,
        label="Test time",
        quantity_total=total,
        quantity_allocated=allocated,
        quantity_unit="hours",
        status=status,
        epoch=0,
    )


def _seed_decision(store: DecisionLedgerStore, decision_id: str) -> None:
    now = "2026-06-19T00:00:00Z"
    store.upsert(
        DecisionRecord(
            id=decision_id,
            actor_id="ROLE-STEWARD-01",
            identity_id=DEFAULT_IDENTITY.id,
            intent="Resource contract test",
            type="operational",
            evidence_refs=[],
            risk_profile={},
            governance_basis={},
            resource_plan={},
            status=DecisionStatus.PROPOSED,
            epoch=0,
            created_at=now,
            updated_at=now,
        )
    )


def _decision_draft(**overrides: object) -> DecisionRecord:
    now = "2026-06-19T00:00:00Z"
    payload = {
        "id": "DEC-TEST-001",
        "actor_id": "ROLE-STEWARD-01",
        "identity_id": DEFAULT_IDENTITY.id,
        "intent": "Contract test decision",
        "type": "operational",
        "evidence_refs": [],
        "risk_profile": {},
        "governance_basis": {},
        "resource_plan": {},
        "status": DecisionStatus.PROPOSED.value,
        "epoch": 0,
        "created_at": now,
        "updated_at": now,
    }
    payload.update(overrides)
    return DecisionRecord.from_dict(payload)


def test_evidence_contract_requires_evidence_refs() -> None:
    contract = EvidenceContract(evidence_store=object())
    decision = _decision_draft(evidence_refs=[])
    with pytest.raises(ValueError, match="requires evidence_refs"):
        contract.check_decision_evidence(decision)


def test_governance_contract_rejects_unauthorized_actor() -> None:
    contract = GovernanceContract(DEFAULT_IDENTITY)
    decision = _decision_draft(
        id="DEC-GOV-001",
        actor_id="ROLE-UNKNOWN",
        type="constitutional-change",
    )
    with pytest.raises(ValueError, match="lacks authority"):
        contract.check_authority(decision)


@pytest.fixture
def resource_contract_stores(tmp_path: Path) -> tuple[ResourceLedgerStore, DecisionLedgerStore]:
    decisions = DecisionLedgerStore(path=tmp_path / "decisions.sqlite3")
    ledger = ResourceLedgerStore(path=tmp_path / "resources.sqlite3")
    return ledger, decisions


def test_resource_allocation_cannot_exceed_total(resource_contract_stores) -> None:
    ledger, decisions = resource_contract_stores
    _seed_decision(decisions, "DEC-1")
    _seed_decision(decisions, "DEC-2")
    ledger.add(_time_resource("RES-1", total=10.0))
    rc = ResourceContract(ledger, decision_ledger=decisions)

    rc.allocate("RES-1", "DEC-1", 6.0, epoch=0)
    assert ledger.get("RES-1").quantity_allocated == 6.0

    with pytest.raises(ValueError, match="exceed total quantity"):
        rc.allocate("RES-1", "DEC-2", 5.0, epoch=0)


def test_resource_status_exhausted_and_release_reactivates(resource_contract_stores) -> None:
    ledger, decisions = resource_contract_stores
    _seed_decision(decisions, "DEC-1")
    ledger.add(_time_resource("RES-2", total=4.0))
    rc = ResourceContract(ledger, decision_ledger=decisions)

    rc.allocate("RES-2", "DEC-1", 4.0, epoch=0)
    exhausted = ledger.get("RES-2")
    assert exhausted is not None
    assert exhausted.status == ResourceStatus.EXHAUSTED

    rc.release("RES-2", "DEC-1", 2.0)
    active = ledger.get("RES-2")
    assert active is not None
    assert active.quantity_allocated == 2.0
    assert active.status == ResourceStatus.ACTIVE


def test_resource_contract_rejects_frozen_allocations(resource_contract_stores) -> None:
    ledger, decisions = resource_contract_stores
    _seed_decision(decisions, "DEC-1")
    ledger.add(_time_resource("RES-3", total=10.0, status=ResourceStatus.FROZEN))
    rc = ResourceContract(ledger, decision_ledger=decisions)
    with pytest.raises(ValueError, match="not allocatable"):
        rc.allocate("RES-3", "DEC-1", 1.0, epoch=0)


def test_resource_contract_quantity_never_negative(resource_contract_stores) -> None:
    ledger, decisions = resource_contract_stores
    _seed_decision(decisions, "DEC-1")
    ledger.add(_time_resource("RES-4", total=10.0, allocated=9.0))
    rc = ResourceContract(ledger, decision_ledger=decisions)
    with pytest.raises(ValueError, match="exceed total quantity"):
        rc.allocate("RES-4", "DEC-1", 2.0, epoch=0)
