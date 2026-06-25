"""Tests for spec-shaped constitutional state model."""

from __future__ import annotations

from datetime import UTC, datetime

from constitutional.runtime import ConstitutionalStateRuntime
from constitutional.runtime.constitutional_state_model import (
    ConstitutionalStateId,
    ConstitutionalStateModel,
    global_to_constitutional_state_object,
    run_constitutional_state_update,
)
from constitutional.runtime.global_constitutional_state import (
    aggregate_global_constitutional_state,
)


def test_model_update_snapshot_matches_global_aggregate() -> None:
    csr = ConstitutionalStateRuntime()
    model = ConstitutionalStateModel(csr)

    obj = model.update_snapshot(snapshot_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC))
    gs = csr.get_global_snapshot()

    assert obj.state_id == ConstitutionalStateId
    assert obj.version == 1
    assert obj.health.score == gs.health.health_score
    assert obj.constitutional_debt.debt_score == gs.constitutional_debt.debt_score
    assert obj.condition == gs.condition


def test_global_to_object_roundtrip_fields() -> None:
    csr = ConstitutionalStateRuntime()
    gs = aggregate_global_constitutional_state(csr)
    obj = global_to_constitutional_state_object(gs)

    assert obj.window == "cumulative"
    assert obj.health.unresolved_divergences == gs.health.unresolved_divergences
    assert len(obj.accountability_chains) == len(gs.accountability.active_accountability_chains)


def test_run_constitutional_state_update_helper() -> None:
    csr = ConstitutionalStateRuntime()
    obj = run_constitutional_state_update(csr)

    assert obj.state_type == "constitutional_state"
    receipts = csr.observation_receipts_for(ConstitutionalStateId)
    assert len(receipts) == 1


def test_collect_helpers_expose_streams() -> None:
    csr = ConstitutionalStateRuntime()
    model = ConstitutionalStateModel(csr)
    now = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)

    receipts = model._collect_receipts_until(now)
    transitions = model._collect_transitions_until(now)

    assert isinstance(receipts, list)
    assert isinstance(transitions, list)
