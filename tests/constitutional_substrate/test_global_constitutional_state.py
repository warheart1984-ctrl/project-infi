"""Tests for global constitutional state (constitutional state spec v0)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from constitutional.core.graph import validate_constitutional_condition_transition
from constitutional.core.models import StateObject
from constitutional.runtime import ConstitutionalStateRuntime
from constitutional.runtime.constitutional_state_scheduler import ConstitutionalStateScheduler
from constitutional.runtime.global_constitutional_state import (
    GLOBAL_STATE_ID,
    ConstitutionalStateAggregator,
    ConstitutionalStateInvariantError,
    aggregate_global_constitutional_state,
    compute_constitutional_debt_score,
    compute_health_score,
    condition_from_health_score,
)
from constitutional.runtime.receipts_v2 import is_receipt_v2_complete
from operator_kernel.constitutional_task import register_operator_task
from operator_kernel.status_mapping import sync_operator_status_to_csr


def test_empty_csr_healthy_snapshot() -> None:
    csr = ConstitutionalStateRuntime()
    state = aggregate_global_constitutional_state(csr)

    assert state.condition == "Healthy"
    assert state.health.health_score == 1.0
    assert state.constitutional_debt.debt_score == 0.0
    assert state.window == "cumulative"


def test_divergent_object_increases_debt_and_lowers_health() -> None:
    csr = ConstitutionalStateRuntime()
    csr.register_state(
        StateObject(state_id="bad", state_type="operator_task", current_state="Closed")
    )

    state = aggregate_global_constitutional_state(csr)

    assert state.health.unresolved_divergences >= 1
    assert state.health.health_score < 1.0
    assert state.constitutional_debt.debt_score > 0.0


def test_aggregator_emits_constitutional_state_receipt() -> None:
    csr = ConstitutionalStateRuntime()
    agg = ConstitutionalStateAggregator(csr)

    state = agg.update_snapshot(snapshot_at=datetime(2026, 6, 23, 7, 30, tzinfo=UTC))

    assert state.state_id == GLOBAL_STATE_ID
    assert state.version == 1
    receipts = csr.observation_receipts_for(GLOBAL_STATE_ID)
    assert len(receipts) == 1
    assert is_receipt_v2_complete(receipts[0])
    assert receipts[0].action_type == "constitutional_state_snapshot"
    assert receipts[0].constitutional_state.debt_score == state.constitutional_debt.debt_score
    assert csr.get_state(GLOBAL_STATE_ID).state_type == "constitutional_state"


def test_happy_path_operator_lowers_risk(csr: ConstitutionalStateRuntime) -> None:
    task_id = "gcs-ok"
    register_operator_task(csr, task_id, goal="gcs test")
    sync_operator_status_to_csr(csr, task_id, {"status": "closed"})

    state = ConstitutionalStateAggregator(csr).update_snapshot(
        snapshot_at=datetime(2026, 6, 23, 8, 0, tzinfo=UTC)
    )

    assert state.health.unresolved_divergences == 0
    assert state.condition == "Healthy"


def test_condition_transition_graph() -> None:
    validate_constitutional_condition_transition("Healthy", "Degraded")
    validate_constitutional_condition_transition("Degraded", "Critical")
    with pytest.raises(ValueError):
        validate_constitutional_condition_transition("Healthy", "Critical")


def test_health_and_debt_score_formulas() -> None:
    low_health = compute_health_score(
        unresolved_divergences=0,
        open_remediations=0,
        overdue_obligations=0,
        pending_amendments=0,
        average_compliance_deficit=0.0,
    )
    high_debt_health = compute_health_score(
        unresolved_divergences=8,
        open_remediations=8,
        overdue_obligations=4,
        pending_amendments=4,
        average_compliance_deficit=0.5,
    )
    assert low_health > high_debt_health
    assert condition_from_health_score(0.9) == "Healthy"
    assert condition_from_health_score(0.6) == "Degraded"
    assert condition_from_health_score(0.2) == "Critical"

    assert compute_constitutional_debt_score(
        unresolved_divergences=0,
        overdue_remediations=0,
        repeated_arbitrations=0,
        recurrent_triggers=0,
    ) == 0.0
    assert compute_constitutional_debt_score(
        unresolved_divergences=10,
        overdue_remediations=5,
        repeated_arbitrations=5,
        recurrent_triggers=10,
    ) == 1.0


def test_cs5_snapshot_at_not_before_receipts(csr: ConstitutionalStateRuntime) -> None:
    register_operator_task(csr, "t1", goal="cs5")
    sync_operator_status_to_csr(csr, "t1", {"status": "closed"})
    state = ConstitutionalStateAggregator(csr).update_snapshot(
        snapshot_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
    )
    assert state.snapshot_at >= datetime(2026, 6, 23, 12, 0, tzinfo=UTC) - timedelta(seconds=1)


def test_scheduler_event_snapshot(csr: ConstitutionalStateRuntime) -> None:
    scheduler = ConstitutionalStateScheduler(transition_threshold=2, interval_seconds=9999)
    scheduler.notify_transition()
    assert scheduler.maybe_snapshot(csr, trigger="transition_threshold") is None
    scheduler.notify_transition()
    state = scheduler.maybe_snapshot(csr, trigger="transition_threshold", force=False)
    assert state is not None
    assert state.version == 1


def test_scheduler_divergence_forces_snapshot(csr: ConstitutionalStateRuntime) -> None:
    scheduler = ConstitutionalStateScheduler()
    state = scheduler.on_divergence(csr)
    assert state is not None
    assert state.health.health_score == 1.0


@pytest.fixture
def csr() -> ConstitutionalStateRuntime:
    return ConstitutionalStateRuntime()
