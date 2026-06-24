"""CRK-1 §4 — Canonical state transition property tests."""

from __future__ import annotations

import pytest

from src.continuity.constitutional_runtime import ConstitutionalRuntime
from src.continuity.decision_ledger import DecisionRecord, DecisionStatus
from src.continuity.resource_ledger import ResourceObject


def test_propose_decision_sets_proposed_status(crk1_runtime: ConstitutionalRuntime) -> None:
    draft = DecisionRecord(
        id="DEC-CRK1-PROP-001",
        actor_id="ROLE-STEWARD-01",
        identity_id=crk1_runtime.ledgers.identity.id,
        intent="Propose-only transition test",
        type="operational",
        evidence_refs=[],
        risk_profile={"level": "low"},
        governance_basis={"process": "crk1-test"},
        resource_plan={},
        status=DecisionStatus.PROPOSED,
        epoch=17,
        tags=["crk1"],
        notes="",
        created_at="2026-06-19T00:00:00Z",
        updated_at="2026-06-19T00:00:00Z",
    )
    saved = crk1_runtime.propose_decision(draft)
    assert saved.status == DecisionStatus.PROPOSED


def test_execute_decision_rejects_unapproved(crk1_runtime: ConstitutionalRuntime) -> None:
    draft = DecisionRecord(
        id="DEC-CRK1-EXEC-001",
        actor_id="ROLE-STEWARD-01",
        identity_id=crk1_runtime.ledgers.identity.id,
        intent="Unapproved execute attempt",
        type="operational",
        evidence_refs=[],
        risk_profile={"level": "low"},
        governance_basis={"process": "crk1-test"},
        resource_plan={},
        status=DecisionStatus.PROPOSED,
        epoch=17,
        tags=["crk1"],
        notes="",
        created_at="2026-06-19T00:00:00Z",
        updated_at="2026-06-19T00:00:00Z",
    )
    crk1_runtime.propose_decision(draft)
    with pytest.raises(ValueError, match="must be approved"):
        crk1_runtime.execute_decision(
            draft.id,
            expected={"metric": 1.0},
            observed={"metric": 1.0},
        )


def test_advance_epoch_blocked_when_spine_unhealthy(
    crk1_runtime: ConstitutionalRuntime, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Runtime contract gates epoch (CRK-1 §4.6)."""

    def _blocked_spine(**kwargs):
        return {
            "epoch_commit_blocked": True,
            "block_reasons": ["OIT-BLOCK"],
            "overall": 0.0,
        }

    monkeypatch.setattr(
        crk1_runtime.contracts["runtime"],
        "build_spine_health",
        _blocked_spine,
    )
    with pytest.raises(RuntimeError, match="Spine unhealthy"):
        crk1_runtime.advance_epoch()


def test_execute_decision_rejects_insufficient_resources(crk1_runtime: ConstitutionalRuntime) -> None:
    crk1_runtime.resources.add(
        ResourceObject(
            id="RES-CRK1-LIMITED",
            type="time",
            label="Limited pool",
            quantity_total=2.0,
            quantity_allocated=0.0,
            quantity_unit="hours",
            epoch=17,
        )
    )
    draft = DecisionRecord(
        id="DEC-CRK1-RES-001",
        actor_id="ROLE-STEWARD-01",
        identity_id=crk1_runtime.ledgers.identity.id,
        intent="Requires more resources than available",
        type="operational",
        evidence_refs=["EVD-CRK1-001"],
        risk_profile={"level": "low"},
        governance_basis={"process": "crk1-test"},
        resource_plan={
            "allocations": [{"resource_id": "RES-CRK1-LIMITED", "amount": 5.0}],
        },
        status=DecisionStatus.PROPOSED,
        epoch=17,
        tags=["crk1"],
        notes="",
        created_at="2026-06-19T00:00:00Z",
        updated_at="2026-06-19T00:00:00Z",
    )
    crk1_runtime.propose_decision(draft)
    crk1_runtime.approve_decision(draft.id)
    with pytest.raises(ValueError, match="insufficient RES-CRK1-LIMITED"):
        crk1_runtime.execute_decision(
            draft.id,
            expected={"metric": 1.0},
            observed={"metric": 1.0},
        )


@pytest.mark.skip(reason="Requires full spine stores bootstrapped healthy")
def test_advance_epoch_succeeds_when_spine_healthy(crk1_runtime: ConstitutionalRuntime) -> None:
    result = crk1_runtime.advance_epoch()
    assert result["epoch"] == crk1_runtime.ledgers.epoch
