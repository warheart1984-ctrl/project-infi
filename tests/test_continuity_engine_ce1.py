"""Tests for Continuity Engine CE-1 — unified axes, thresholds, kernel, and forecast."""

from __future__ import annotations

from datetime import UTC, datetime

from src.continuity.stewardability.lineage_event_log import (
    LineageActor,
    LineageEventLog,
    LineageInsight,
    LineageOrigin,
    record_lineage_event,
)
from src.continuity.stewardability.operating_conditions import good_conditions
from src.cos1 import ContinuityOS
from src.cos1.accumulation import (
    AccumulationEventLog,
    AccumulationFields,
    AccumulationInsight,
    record_accumulation_event,
)
from src.cos1.continuity_engine import (
    ContinuityEngine,
    ContinuityEngineEventLog,
    assess_continuity_thresholds,
    assess_mat3_ce1,
    assess_pt3,
    assess_ct2,
    compute_state_vector,
    forecast_ce1,
    record_ce_event,
)


def _actor(actor_id: str, domain: str = "psychology") -> LineageActor:
    return LineageActor(id=actor_id, domain=domain, exposed_to_jpss=False)


def _insight(text: str) -> LineageInsight:
    return LineageInsight(
        text=text,
        lineage_compatible=True,
        novelty_level="INDEPENDENT_EXPLANATION",
        structural_alignment=["calibration", "drift"],
    )


def _acc_insight(text: str) -> AccumulationInsight:
    return AccumulationInsight(
        text=text,
        lineage_compatible=True,
        novelty_level="INDEPENDENT_EXPLANATION",
        structural_alignment=["calibration", "drift"],
    )


def _seed_jon_lineage_phase3(
    lineage_log: LineageEventLog,
    accumulation_log: AccumulationEventLog,
) -> None:
    """Seed events placing Jon/Sue lineage in Phase 3 — Accumulation, approaching Steward Emergence."""
    # Propagation (PT-3): 3 events
    for actor_id, domain in [("sue", "psychology"), ("alex", "education"), ("maria", "systems")]:
        record_lineage_event(
            lineage_log,
            actor=_actor(actor_id, domain),
            insight=_insight(f"{actor_id} propagates calibration-drift insight."),
            origin=LineageOrigin(type="PROPAGATION"),
            event_id=f"prop-{actor_id}",
        )

    # Convergence (CT-2): 2 events across 2 domains
    record_lineage_event(
        lineage_log,
        actor=_actor("independent-1", "engineering"),
        insight=_insight("Independent rediscovery of drift boundary."),
        origin=LineageOrigin(type="CONVERGENCE"),
        event_id="conv-eng-1",
    )
    record_lineage_event(
        lineage_log,
        actor=_actor("independent-2", "medicine"),
        insight=_insight("Cross-domain convergence on calibration invariants."),
        origin=LineageOrigin(type="CONVERGENCE"),
        event_id="conv-med-1",
    )

    # Accumulation chain: sue → alex → maria (A1 → A4 → A2)
    record_accumulation_event(
        accumulation_log,
        actor=_actor("sue", "psychology"),
        insight=_acc_insight("Calibration can drift while knowledge persists."),
        accumulation=AccumulationFields(strengthened_explanation=True),
        event_id="acc-sue-a1",
    )
    record_accumulation_event(
        accumulation_log,
        actor=_actor("alex", "education"),
        insight=_acc_insight("Structural deepening of drift detection."),
        accumulation=AccumulationFields(
            structural_deepening=True,
            builds_on_event_ids=["acc-sue-a1"],
            returns_stronger=True,
        ),
        event_id="acc-alex-a2",
    )
    record_accumulation_event(
        accumulation_log,
        actor=_actor("maria", "systems"),
        insight=_acc_insight("Integrative synthesis across domains."),
        accumulation=AccumulationFields(
            integrative_synthesis=True,
            builds_on_event_ids=["acc-alex-a2"],
            returns_stronger=True,
        ),
        event_id="acc-maria-a3",
    )

    # Mirror propagation events for accumulation IDs in lineage log
    for event_id, actor_id, domain, origin in [
        ("acc-sue-a1", "sue", "psychology", "PROPAGATION"),
        ("acc-alex-a2", "alex", "education", "PROPAGATION"),
        ("acc-maria-a3", "maria", "systems", "CONVERGENCE"),
    ]:
        record_lineage_event(
            lineage_log,
            actor=_actor(actor_id, domain),
            insight=_insight(f"Lineage mirror for {event_id}."),
            origin=LineageOrigin(type=origin),  # type: ignore[arg-type]
            event_id=event_id,
        )


def test_ce_json_unified_event_axes() -> None:
    log = ContinuityEngineEventLog()
    record_ce_event(
        log,
        actor=_actor("sue"),
        insight=_insight("Propagation signal."),
        origin=LineageOrigin(type="PROPAGATION"),
        accumulation=AccumulationFields(strengthened_explanation=True),
    )
    assert len(log.propagation_events()) == 1
    assert len(log.accumulation_events()) == 1
    assert log.events[0].accumulation.signature == "A1"


def test_pt3_ct2_mat3_thresholds() -> None:
    lineage = LineageEventLog()
    accumulation = AccumulationEventLog()
    _seed_jon_lineage_phase3(lineage, accumulation)

    engine = ContinuityEngine()
    ce_log = engine.build_log(lineage, accumulation)

    pt3 = assess_pt3(ce_log)
    ct2 = assess_ct2(ce_log)
    mat3 = assess_mat3_ce1(ce_log)

    assert pt3.met is True
    assert pt3.count >= 3
    assert ct2.met is True
    assert ct2.domain_count >= 2
    assert mat3.met is True
    assert mat3.count >= 3

    thresholds = assess_continuity_thresholds(ce_log)
    assert thresholds.continuity_mode is True


def test_ce1_phase3_accumulation_approaching_steward_emergence() -> None:
    lineage = LineageEventLog()
    accumulation = AccumulationEventLog()
    _seed_jon_lineage_phase3(lineage, accumulation)

    engine = ContinuityEngine()
    assessment = engine.assess_from_memory(lineage, accumulation)

    assert assessment.phase == "accumulation"
    assert assessment.state.P >= 3
    assert assessment.state.C >= 2
    assert assessment.state.A >= 3
    assert assessment.thresholds.continuity_mode is True
    assert assessment.forecast.approaching_steward_emergence is True
    assert assessment.forecast.stewardship_likely is True


def test_compounding_dominance_with_prior_state() -> None:
    lineage = LineageEventLog()
    accumulation = AccumulationEventLog()
    _seed_jon_lineage_phase3(lineage, accumulation)

    engine = ContinuityEngine()
    prior = compute_state_vector(engine.build_log(lineage, AccumulationEventLog()))
    assessment = engine.assess_from_memory(lineage, accumulation, prior_state=prior)

    assert assessment.compounding_dominance is not None
    assert assessment.compounding_dominance.delta_accumulation >= 3


def test_continuity_kernel_k1_k3() -> None:
    log = ContinuityEngineEventLog()
    record_ce_event(
        log,
        actor=_actor("sue"),
        insight=_insight("Coherent extension."),
        origin=LineageOrigin(type="PROPAGATION"),
        accumulation=AccumulationFields(
            strengthened_explanation=True,
            returns_stronger=True,
        ),
    )
    engine = ContinuityEngine()
    assessment = engine.assess(log)
    assert assessment.kernel.all_satisfied is True


def test_ce_forecast_logistic() -> None:
    lineage = LineageEventLog()
    accumulation = AccumulationEventLog()
    _seed_jon_lineage_phase3(lineage, accumulation)
    state = compute_state_vector(ContinuityEngine().build_log(lineage, accumulation))
    result = forecast_ce1(state)
    assert 0.0 <= result.probability <= 1.0
    assert result.phase in {"accumulation", "steward_emergence", "stewardability"}


def test_cos1_step_includes_ce1() -> None:
    os = ContinuityOS()
    _seed_jon_lineage_phase3(
        os.memory.get_lineage_event_log(),
        os.memory.get_accumulation_event_log(),
    )
    result = os.step(good_conditions())
    assert result.ce1 is not None
    assert result.ce1.continuity_mode is True
    assert result.ce1.phase == "accumulation"
    assert result.ce1.forecast.approaching_steward_emergence is True
