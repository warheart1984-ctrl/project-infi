"""Tests for JPSS Lineage Event Log v0.1 and propagation/convergence disambiguation."""

from __future__ import annotations

from src.continuity.stewardability.concept_resonance import (
    concept_resonance_to_lineage_event,
    sue_reference_event,
)
from src.continuity.stewardability.lineage_axes import assess_dual_axes
from src.continuity.stewardability.lineage_disambiguation import disambiguate_lineage_event
from src.continuity.stewardability.lineage_event_log import (
    LineageActor,
    LineageEvent,
    LineageEventLog,
    LineageInsight,
    LineageOrigin,
    OriginEvidence,
    sue_reference_lineage_event,
)
from src.cos1.continuity_os import ContinuityOS
from src.cos1.memory import ContinuityMemory
from tests.test_stewardability_cos1 import good_conditions


def test_concept_resonance_maps_to_ambiguous_lineage_event() -> None:
    sue = sue_reference_event()
    lineage = concept_resonance_to_lineage_event(sue)

    assert lineage.origin.type == "AMBIGUOUS"
    assert lineage.origin.possible == ["PROPAGATION", "CONVERGENCE"]
    assert lineage.actor.exposed_to_jpss is False
    assert lineage.insight.novelty_level == "INDEPENDENT_EXPLANATION"
    assert "calibration" in lineage.insight.structural_alignment
    assert "drift" in lineage.insight.structural_alignment


def test_sue_disambiguates_to_convergence() -> None:
    sue_lineage = sue_reference_lineage_event()
    resolved, result = disambiguate_lineage_event(sue_lineage)

    assert result.prior_type == "AMBIGUOUS"
    assert result.resolved_type == "CONVERGENCE"
    assert resolved.origin.type == "CONVERGENCE"
    assert result.confidence == "HIGH"


def test_exposed_event_disambiguates_to_propagation() -> None:
    event = LineageEvent(
        event_id="evt-prop-001",
        timestamp=sue_reference_lineage_event().timestamp,
        actor=LineageActor(id="alex", domain="engineering", exposed_to_jpss=True),
        insight=LineageInsight(
            text="Calibration drift can break judgment continuity under load.",
            lineage_compatible=True,
            novelty_level="VARIATION",
            structural_alignment=["calibration", "drift"],
        ),
        origin=LineageOrigin(
            type="AMBIGUOUS",
            possible=["PROPAGATION", "CONVERGENCE"],
            evidence=OriginEvidence(causal_influence_plausible=True),
        ),
    )
    resolved, result = disambiguate_lineage_event(event)

    assert result.resolved_type == "PROPAGATION"
    assert resolved.origin.type == "PROPAGATION"


def test_memory_syncs_lineage_log_from_resonance() -> None:
    memory = ContinuityMemory()
    memory.get_concept_resonance_register().append(sue_reference_event())

    added = memory.sync_lineage_log_from_resonance()
    assert added == 1

    log = memory.get_lineage_event_log()
    assert len(log.events) == 1
    assert log.events[0].origin.type == "AMBIGUOUS"


def test_dual_axes_reports_convergence_for_sue() -> None:
    log = LineageEventLog()
    log.append(sue_reference_lineage_event())

    assessment = assess_dual_axes(log)
    assert assessment.reality.signal_count == 1
    assert assessment.transmission.signal_count == 0
    assert assessment.ambiguous_pending == 0


def test_cos1_step_reports_lineage_axes() -> None:
    os = ContinuityOS()
    os.memory.get_concept_resonance_register().append(sue_reference_event())

    result = os.step(good_conditions())
    assert result.lineage_axes is not None
    assert result.lineage_axes.reality.signal_count == 1
    assert result.lineage_axes.dov_reached is False
