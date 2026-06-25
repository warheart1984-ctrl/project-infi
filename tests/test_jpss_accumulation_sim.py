"""Tests for minimal RA-COS-1 JPSS accumulation simulation (Sue/Bradley MAT-3)."""

from __future__ import annotations

from src.continuity.ra.jpss_accumulation_sim import (
    JUDGMENT_ARCHITECTURE_LAYERS,
    JUDGMENT_TRANSMISSION_CARRIERS,
    css1_accumulation_classification,
    event_bradley_judgment_transmission,
    event_sue_calibration_drift,
    has_reached_mat3,
    ingest_event,
    mat3_assessment,
    simulate_sue_bradley_mat3,
)


def test_sue_and_bradley_css1_classification() -> None:
    sue = css1_accumulation_classification(event_sue_calibration_drift())
    bradley = css1_accumulation_classification(event_bradley_judgment_transmission())

    assert sue["actor"] == "Sue"
    assert "Explanatory Deepening" in sue["type"]
    assert sue["axis"] == "Continuity"

    assert bradley["actor"] == "Bradley"
    assert "Structural Deepening" in bradley["type"]
    assert bradley["axis"] == "Transferability"
    assert bradley["complementary_pattern"]


def test_bradley_carriers_are_cos1_territory() -> None:
    bradley = event_bradley_judgment_transmission()
    assert set(bradley.judgment_carriers) == set(JUDGMENT_TRANSMISSION_CARRIERS)
    assert len(JUDGMENT_ARCHITECTURE_LAYERS) == 3


def test_mat3_flips_false_to_true_on_third_event() -> None:
    state, trace = simulate_sue_bradley_mat3(include_jon_seed=True)

    assert trace[0]["reached"] is False
    assert trace[1]["reached"] is False
    assert trace[2]["reached"] is True

    assert has_reached_mat3(state)
    assert state.accumulation_count >= 3
    assert len(state.actor_set) >= 2
    assert "Sue" in state.actor_set
    assert "Bradley" in state.actor_set


def test_mat3_requires_a2_or_higher() -> None:
    from src.continuity.ra.jpss_accumulation_sim import RAAccumulationState

    state = RAAccumulationState()
    for _ in range(3):
        state = ingest_event(state, event_sue_calibration_drift())
    assert has_reached_mat3(state) is False
    assessment = mat3_assessment(state)
    assert any("A2" in blocker for blocker in assessment["blockers"])


def test_complementary_not_redundant_pattern() -> None:
    state, _ = simulate_sue_bradley_mat3()
    sue = next(e for e in state.events if e.actor == "Sue")
    bradley = next(e for e in state.events if e.actor == "Bradley")

    assert sue.accumulation_type == "A1"
    assert bradley.accumulation_type == "A2"
    assert bradley.builds_on == ["E_Sue"]
    assert sue.targets_layer == "Continuity"
    assert bradley.targets_layer == "Transferability"
