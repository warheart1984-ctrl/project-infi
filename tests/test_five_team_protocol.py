"""Tests for Five-Team adversarial protocol scoring."""

from __future__ import annotations

from simulation.five_team_protocol import (
    AttackRecord,
    CampaignState,
    DriftAssessment,
    build_round_protocol,
    classify_continuity_signal,
    detect_kernel_failure,
    evaluate_amendment_triggers,
    score_attack,
    should_stop_campaign,
)
from simulation.five_team_loop import run_campaign, run_round


def test_attack_score_max_10() -> None:
    assert score_attack(4, 3, 3) == 10
    assert score_attack(0, 0, 0) == 0


def test_drift_index_max_12() -> None:
    drift = DriftAssessment(round_id=1, definition_drift=4, rule_drift=4, behavior_drift=4)
    assert drift.drift_index == 12


def test_doctrine_mode_signal() -> None:
    assert classify_continuity_signal(drift_index=9, attack_score=3) == "doctrine_mode"


def test_rigid_fragile_signal() -> None:
    assert classify_continuity_signal(drift_index=2, attack_score=8) == "rigid_fragile"


def test_healthy_signal() -> None:
    assert classify_continuity_signal(drift_index=2, attack_score=2) == "healthy"


def test_amendment_trigger_a_repeated_attacks() -> None:
    rounds = []
    for round_id in range(1, 4):
        rounds.append(
            build_round_protocol(
                round_id,
                adm_drift_score=0.7,
                adm_high_drift=True,
                k4_satisfied=False,
                crk1_compliant=True,
                psd_aggregate=0.6,
                chaos_results=[],
                invariant_target="K4",
                prior_rounds=rounds,
            )
        )
    triggers = evaluate_amendment_triggers(rounds)
    trigger_a = next(trigger for trigger in triggers if trigger.trigger == "A")
    assert trigger_a.fired is True


def test_kernel_failure_break_1() -> None:
    protocol = build_round_protocol(
        1,
        adm_drift_score=0.2,
        adm_high_drift=False,
        k4_satisfied=False,
        crk1_compliant=False,
        psd_aggregate=0.1,
        chaos_results=[],
        invariant_target="K4",
    )
    for record in protocol.invariant_records:
        if record.invariant_id in {"K3", "K4"}:
            record.status = "broken"
    failure = detect_kernel_failure([protocol])
    assert failure is not None
    assert failure.break_id == "break_1"


def test_round_includes_protocol() -> None:
    result = run_round(1)
    assert result.protocol is not None
    assert result.protocol.max_attack_score >= 0
    assert result.protocol.drift_index >= 0
    assert len(result.protocol.attacks) >= 2


def test_campaign_runs_minimum_rounds() -> None:
    campaign = run_campaign(min_rounds=3, max_rounds=5)
    assert campaign.rounds_completed >= 3
    assert campaign.stop_reason is not None


def test_non_trivial_attack_detection() -> None:
    attack = AttackRecord(
        round_id=1,
        team="red",
        attack_id="r1",
        target="K4",
        description="test",
        severity=2,
        novelty=1,
        exploitability=1,
    )
    assert attack.attack_score == 4
    assert attack.is_non_trivial is True


def test_stopping_before_min_rounds() -> None:
    state = CampaignState(config=__import__("simulation.five_team_protocol", fromlist=["CampaignConfig"]).CampaignConfig(min_rounds=10))
    stop, reason = should_stop_campaign(state)
    assert stop is False
    assert reason is None
