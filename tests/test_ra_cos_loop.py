"""End-to-end RA-COS-1 loop: triggers → governance → registry → ledger."""

from __future__ import annotations

import pytest

from src.continuity.css2 import (
    RecalibrationGovernanceEngine,
    RecalibrationLedger,
    SystemState,
    Threshold,
    default_recalibration_rule,
    seed_css1_thresholds,
)
from src.continuity.css2.threshold_store import RacosThresholdStore
from src.continuity.ra.ra_cos_loop import (
    build_recalibration_proposal,
    process_ra_cos_event,
    propose_new_threshold_value,
)
from src.continuity.ra.recalibration_triggers import RecalibrationTrigger


def test_ra_cos_loop_late_intervention_updates_registry_and_ledger():
    thresholds = seed_css1_thresholds()
    th = next(t for t in thresholds if t.metric == "propagation_count")
    original_value = th.value

    ledger = RecalibrationLedger()
    engine = RecalibrationGovernanceEngine(ledger=ledger)
    state = SystemState(thresholds=thresholds, recalibration_rule=default_recalibration_rule())

    result = process_ra_cos_event(
        {"metric": th.metric, "domain": th.domain},
        drift_signals={},
        validation={"late_intervention": True},
        state=state,
        governance=engine,
    )

    assert result.triggers
    assert any(t.reason == "late_intervention" for t in result.triggers)
    assert any(e.decision == "approved" for e in result.events)
    assert len(ledger.events) >= 1

    updated = next(t for t in result.thresholds if t.id == th.id)
    assert updated.value == propose_new_threshold_value(th, result.triggers[0])
    assert updated.value != original_value
    assert updated.last_updated_by != th.last_updated_by or updated.value != th.value


def test_ra_cos_loop_crk_rejects_safety_weakening():
    safety = Threshold(
        id="T_safety_override_001",
        name="Safety override threshold",
        domain="Safety.core",
        metric="safety_violations_per_hour",
        comparator=">",
        value=0,
        intent="Any safety violation triggers immediate halt.",
        created_by="Founder",
        last_updated_by="Founder",
    )
    ledger = RecalibrationLedger()
    engine = RecalibrationGovernanceEngine(ledger=ledger)
    state = SystemState(thresholds=[safety], recalibration_rule=default_recalibration_rule())

    result = process_ra_cos_event(
        {"metric": safety.metric, "domain": safety.domain},
        drift_signals={},
        validation={"over_intervention_count": 5, "metric": safety.metric},
        state=state,
        governance=engine,
    )

    assert any(e.decision == "rejected" for e in result.events)
    assert "INV_001_HALT_ON_SAFETY" in result.events[0].legitimacy_basis
    assert len(ledger.events) >= 1

    current = next(t for t in result.thresholds if t.id == safety.id)
    assert current.value == 0


def test_build_recalibration_proposal_maps_ra_trigger():
    th = seed_css1_thresholds()[0]
    ra_trig = RecalibrationTrigger(
        threshold_id=th.id,
        reason="drift_signal",
        evidence=[{"psd_score": 0.7}],
    )
    after = th.model_copy(update={"value": th.value})
    from src.continuity.css2.threshold import ThresholdDelta

    delta = ThresholdDelta(
        threshold_id=th.id,
        before=th,
        after=after,
        rationale="test",
    )
    ctx = build_recalibration_proposal(
        ra_trigger=ra_trig,
        threshold=th,
        delta=delta,
        evidence=ra_trig.evidence,
    )
    assert ctx.triggers
    assert ctx.triggers[0].trigger_type == "drift"
    assert ctx.triggers[0].is_legitimate
    assert ctx.proposed_changes[0].metric_id == th.metric


def test_ra_cos_loop_persists_approval_to_sqlite(tmp_path):
    store = RacosThresholdStore(path=tmp_path / "ra_cos.sqlite3")
    thresholds = seed_css1_thresholds()
    store.seed_from_list(thresholds)
    th = next(t for t in thresholds if t.metric == "propagation_count")
    original_value = th.value

    ledger = RecalibrationLedger()
    engine = RecalibrationGovernanceEngine(ledger=ledger)
    state = SystemState(thresholds=store.load_thresholds(), recalibration_rule=default_recalibration_rule())

    process_ra_cos_event(
        {"metric": th.metric, "domain": th.domain},
        {},
        {"late_intervention": True},
        state,
        governance=engine,
        store=store,
    )

    persisted = store.get_threshold(th.id)
    assert persisted is not None
    assert persisted.value != original_value
    history = store.get_history(th.id)
    assert len(history) >= 2
    approved = store.list_recalibration_events(decision="approved", limit=10)
    assert approved


def test_ra_cos_loop_persists_rejection_without_registry_change(tmp_path):
    store = RacosThresholdStore(path=tmp_path / "ra_cos.sqlite3")
    safety = Threshold(
        id="T_safety_override_001",
        name="Safety override threshold",
        domain="Safety.core",
        metric="safety_violations_per_hour",
        comparator=">",
        value=0,
        intent="Any safety violation triggers immediate halt.",
        created_by="Founder",
        last_updated_by="Founder",
    )
    store.seed_from_list([safety])

    ledger = RecalibrationLedger()
    engine = RecalibrationGovernanceEngine(ledger=ledger)
    state = SystemState(thresholds=store.load_thresholds(), recalibration_rule=default_recalibration_rule())

    process_ra_cos_event(
        {"metric": safety.metric, "domain": safety.domain},
        {},
        {"over_intervention_count": 5, "metric": safety.metric},
        state,
        governance=engine,
        store=store,
    )

    current = store.get_threshold(safety.id)
    assert current is not None
    assert current.value == 0
    rejected = store.list_recalibration_events(decision="rejected", limit=10)
    assert rejected
    assert len(store.get_history(safety.id)) == 1
