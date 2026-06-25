"""Tests for AE-JSON-1, ADF-1 classifier, MAT-3 chain detector, and forecast model."""

from __future__ import annotations

from datetime import UTC, datetime

from src.continuity.stewardability.lineage_event_log import LineageActor
from src.continuity.stewardability.operating_conditions import good_conditions
from src.cos1 import ContinuityOS
from src.cos1.accumulation import (
    AccumulationEventLog,
    AccumulationFields,
    AccumulationInsight,
    assess_mat3,
    classify_accumulation,
    detect_compounding_chains,
    forecast_stewardability,
    record_accumulation_event,
    ClassifiedAccumulationEvent,
    LineageMetrics,
)


def _actor(actor_id: str, domain: str = "psychology") -> LineageActor:
    return LineageActor(id=actor_id, domain=domain, exposed_to_jpss=False)


def _insight(text: str) -> AccumulationInsight:
    return AccumulationInsight(
        text=text,
        lineage_compatible=True,
        novelty_level="INDEPENDENT_EXPLANATION",
        structural_alignment=["calibration", "drift"],
    )


def test_classify_accumulation_adf1_priority() -> None:
    assert classify_accumulation(AccumulationFields(strengthened_explanation=True)) == "A1"
    assert classify_accumulation(AccumulationFields(structural_deepening=True)) == "A2"
    assert classify_accumulation(AccumulationFields(integrative_synthesis=True)) == "A3"
    assert classify_accumulation(
        AccumulationFields(builds_on_event_ids=["evt-a"])
    ) == "A4"
    assert classify_accumulation(AccumulationFields()) == "NONE"
    assert (
        classify_accumulation(
            AccumulationFields(
                integrative_synthesis=True,
                builds_on_event_ids=["evt-a"],
            )
        )
        == "A3"
    )


def test_detect_multi_actor_compounding_chain() -> None:
    events = [
        ClassifiedAccumulationEvent(
            event_id="evt-a",
            actor_id="sue",
            accumulation_signature="A1",
            builds_on_event_ids=[],
        ),
        ClassifiedAccumulationEvent(
            event_id="evt-b",
            actor_id="alex",
            accumulation_signature="A4",
            builds_on_event_ids=["evt-a"],
        ),
        ClassifiedAccumulationEvent(
            event_id="evt-c",
            actor_id="maria",
            accumulation_signature="A2",
            builds_on_event_ids=["evt-b"],
        ),
    ]
    chains = detect_compounding_chains(events)
    assert chains
    multi = [chain for chain in chains if len(set(chain.actors)) >= 2]
    assert multi
    assert max(chain.length for chain in chains) >= 3

    mat3 = assess_mat3(events)
    assert mat3.threshold_met is True
    assert mat3.multi_actor_chain_count >= 1
    assert mat3.max_chain_length >= 2


def test_record_accumulation_event_assigns_signature() -> None:
    log = AccumulationEventLog()
    event = record_accumulation_event(
        log,
        actor=_actor("sue"),
        insight=_insight("Calibration can drift while knowledge persists."),
        accumulation=AccumulationFields(strengthened_explanation=True),
        event_id="evt-sue-ae1",
    )
    assert event.accumulation.signature == "A1"
    assert len(log.accumulation_events()) == 1


def test_forecast_stewardability_phases() -> None:
    early = forecast_stewardability(LineageMetrics())
    assert early.phase == "EARLY"
    assert early.probability < 0.25

    rich = forecast_stewardability(
        LineageMetrics(
            propagation=5,
            convergence=4,
            accumulation=6,
            avg_chain_length=3.0,
            cross_domain_spread=4,
        )
    )
    assert rich.probability > 0.5
    assert rich.phase in {"COMPOUNDING", "NEAR_STEWARDABILITY"}


def test_cos1_step_includes_accumulation_and_forecast() -> None:
    os = ContinuityOS()
    log = os.memory.get_accumulation_event_log()
    record_accumulation_event(
        log,
        actor=_actor("sue", "psychology"),
        insight=_insight("First compounding insight."),
        accumulation=AccumulationFields(strengthened_explanation=True),
    )
    result = os.step(good_conditions())
    assert result.accumulation_mat3 is not None
    assert result.stewardability_forecast is not None
    assert result.stewardability_forecast.metrics.accumulation >= 1
