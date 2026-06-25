"""Tests for collapsed stack — CRK-1 → RA-COS-1 → AAIS → LLM."""

from __future__ import annotations

from src.continuity.ra.jpss_accumulation_sim import JPSSContributionEvent
from src.stack import (
    GovernedStack,
    GovernedStackRequest,
    assess_falsification,
    classify_mode,
    compute_epistemic_metrics,
    run_task_planning_slice,
    tag_contribution_event,
)
from src.stack.aais_runtime import AAISRuntime, MockLLMAdapter
from src.stack.crk1_api import CRK1Kernel
from src.stack.falsification import compute_fm1_observation_delta, compute_fm3_interpretation_drift_index
from src.stack.ra_cos1_api import RACOS1Layer


def test_epistemic_mode_classification() -> None:
    from datetime import UTC, datetime

    obs = JPSSContributionEvent(
        id="e1",
        actor="observer",
        timestamp=datetime.now(UTC),
        source_text="Calibration drift observed.",
        from_exposure=False,
        mode="OBSERVATION",
        origin="PLA",
    )
    assert classify_mode(obs) == "OBSERVATION"
    metrics = compute_epistemic_metrics([obs])
    assert metrics.observation_count == 1


def test_fm1_observation_delta() -> None:
    weak = compute_fm1_observation_delta(
        jps_trained_observation_score=0.4,
        control_observation_score=0.6,
    )
    assert weak.instrument_hypothesis_weakens is True

    strong = compute_fm1_observation_delta(
        jps_trained_observation_score=0.8,
        control_observation_score=0.4,
    )
    assert strong.instrument_hypothesis_weakens is False


def test_fm3_doctrine_detection() -> None:
    from src.stack.epistemic import EpistemicMetrics

    epistemic = EpistemicMetrics(observation_count=1, interpretation_count=5)
    fm3 = compute_fm3_interpretation_drift_index(epistemic)
    assert fm3.instrument_hypothesis_weakens is True


def test_crk1_blocks_destructive_intent() -> None:
    kernel = CRK1Kernel()
    result = kernel.check_invariant(
        actor_id="operator",
        intent="delete all records and bypass governance",
    )
    assert result.allowed is False
    assert len(result.violations) >= 2


def test_ra_cos1_logs_oiv_events() -> None:
    layer = RACOS1Layer()
    obs = layer.log_observation(actor="human", text="Team task backlog observed.")
    interp = layer.log_interpretation(actor="aais", text="Plan: preserve IDs.", builds_on=[obs.id])
    layer.run_validation(interp.id)

    health = layer.get_continuity_health(jps_trained_score=0.7, control_score=0.3)
    assert health.event_count >= 3
    assert health.epistemic.validation_count >= 1


def test_governed_stack_call_chain() -> None:
    stack = GovernedStack()
    response = stack.handle_request(
        GovernedStackRequest(
            actor_id="team-lead",
            prompt="Plan sprint tasks for three engineers.",
        )
    )
    assert response.allowed is True
    assert "CRK-1 → RA-COS-1" in " ".join(response.call_chain)
    assert response.health.event_count >= 2


def test_aais_emits_jpss_events() -> None:
    continuity = RACOS1Layer()
    aais = AAISRuntime(continuity=continuity, llm=MockLLMAdapter())
    response, check = aais.complete("Create a task plan for the team.")
    assert check.allowed
    assert response.text
    modes = {event.mode for event in aais.last_events()}
    assert "OBSERVATION" in modes
    assert "INTERPRETATION" in modes


def test_falsification_assessment_channels() -> None:
    from datetime import UTC, datetime

    events = [
        tag_contribution_event(
            JPSSContributionEvent(
                id="i1",
                actor="a",
                timestamp=datetime.now(UTC),
                source_text="Interpretation without observation.",
                from_exposure=True,
                mode="INTERPRETATION",
                origin="LA",
            )
        )
        for _ in range(4)
    ]
    result = assess_falsification(events, jps_trained_observation_score=0.2, control_observation_score=0.5)
    assert "F1_no_observational_improvement" in result.channels_triggered
    assert result.instrument_hypothesis_holds is False


def test_task_planning_vertical_slice() -> None:
    result = run_task_planning_slice()
    assert result.call_chain_verified
    assert result.scenarios[0].allowed is True
    assert result.blocked_scenario is not None
    assert result.blocked_scenario.allowed is False
