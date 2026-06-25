"""Tests for Five-Team Continuity Simulation Loop."""

from __future__ import annotations

from simulation.five_team_loop import (
    compute_gold_metrics,
    evaluate_white_survival,
    inject_chaos_scenarios,
    run_black_chaos_smoke,
    run_round,
)


def test_gold_metrics_phase35() -> None:
    gold = compute_gold_metrics(round_id=1)
    assert gold.ce_p >= 3
    assert gold.ce_c >= 2
    assert gold.ce_a >= 3
    assert gold.css_phase == "pre_stewardship_compounding"
    assert gold.k4_satisfied is True
    assert gold.crk1_compliant is True


def test_black_chaos_scenarios_exist() -> None:
    scenarios = inject_chaos_scenarios()
    assert len(scenarios) >= 2
    assert any(s.name == "acceptance_without_validation" for s in scenarios)


def test_black_smoke_reality_veto() -> None:
    results = run_black_chaos_smoke()
    veto = next(r for r in results if r["scenario"] == "acceptance_without_validation")
    assert veto["chaos_test_passed"] is True
    assert veto["vas_validated"] is False


def test_white_survival_from_gold() -> None:
    gold = compute_gold_metrics(1)
    white = evaluate_white_survival(gold)
    assert white.system_survived in ("yes", "conditional", "no")
    assert white.crk_amendment_required is False


def test_full_round_runs() -> None:
    result = run_round(1)
    assert result.gold is not None
    assert result.white is not None
    assert len(result.chaos_results) >= 2
