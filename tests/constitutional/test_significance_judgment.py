"""Significance Judgment Test v1 — runtime and succession gate tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.significance.reference_lattice import (
    SIGNIFICANCE_JUDGMENT_PASS_SCORE,
    get_reference_lattice,
)
from constitutional.significance.significance_governance import (
    succession_significance_continuity_ready,
    succession_significance_evolution_ready,
    succession_significance_judgment_ready,
)
from constitutional.significance.significance_judgment_runtime import (
    SignificanceJudgmentRuntime,
    StewardSignificanceAnswer,
    check_succession_readiness,
    seed_passing_significance_judgment,
)
from operator_kernel.succession import succession_blocked, succession_ready


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_domain_memory_index()


@pytest.fixture
def csr(tmp_path) -> ConstitutionalStateRuntime:
    from constitutional.core.articles import PURPOSE_CONTINUITY_INVARIANT

    runtime = ConstitutionalStateRuntime(persist_root=tmp_path)
    runtime.register_invariant(PURPOSE_CONTINUITY_INVARIANT, "Article P")
    runtime.register_invariant(
        "CRITICAL_SYSTEMS_MUST_REMAIN_RECONSTRUCTABLE",
        "Article R",
    )
    return runtime


def _dashboard(**kwargs):
    from constitutional.runtime.reconstructability_dashboard_runtime import (
        ReconstructabilityDashboardState,
    )

    defaults = dict(
        snapshot_at=datetime.now(UTC).replace(microsecond=0),
        version=1,
        system_survivability_score=0.8,
        steward_independence_score=0.8,
        founder_dependency_index=0.2,
        reconstructability_fitness_score=0.8,
        constitutional_debt_score=0.1,
        constitutional_risk_score=0.1,
        personal_capacity_continuity=0.8,
        purpose_continuity_index=0.85,
        mission_legibility_score=1.0,
        invariant_interpretation_score=0.85,
        mission_fidelity={"interactive_passed": True},
    )
    defaults.update(kwargs)
    return ReconstructabilityDashboardState(**defaults)


def _fitness(**kwargs):
    from constitutional.runtime.reconstructability_fitness_runtime import (
        ReconstructabilityFitnessState,
    )

    defaults = dict(
        snapshot_at=datetime.now(UTC).replace(microsecond=0),
        version=1,
        fitness_score=0.85,
        stewardship_readiness_score=0.85,
    )
    defaults.update(kwargs)
    return ReconstructabilityFitnessState(**defaults)


def _passing_answers() -> dict[str, StewardSignificanceAnswer]:
    return {
        "artifact_a": StewardSignificanceAnswer(
            artifact_id="artifact_a",
            tier=0,
            rationale=(
                "Emergency steward bypass concentrates hidden authority and violates Tier 0 "
                "anti-corruption and anti-capture invariants; it threatens Purpose Continuity."
            ),
            invariant_links=["ANTI_CORRUPTION", "ANTI_CAPTURE", "PURPOSE_CONTINUITY"],
            purpose_links=["Purpose Continuity"],
            evidence_that_would_change=["Dual-control emergency scope with automatic sunset"],
            consequences=["Misclassification enables constitutional capture"],
        ),
        "artifact_b": StewardSignificanceAnswer(
            artifact_id="artifact_b",
            tier=2,
            rationale=(
                "Seasonal environmental context is a contextual frame (Tier 2) shaping "
                "interpretation without altering core doctrine; preserve for continuity."
            ),
            invariant_links=["CONTEXTUAL_INTERPRETATION"],
            purpose_links=["interpretation continuity"],
            evidence_that_would_change=["Direct Tier 0 override would reclassify upward"],
            consequences=["Treating context as doctrine causes cargo-cult drift"],
        ),
        "artifact_c": StewardSignificanceAnswer(
            artifact_id="artifact_c",
            tier=3,
            rationale=(
                "Organic steward cultural ritual is a historical artifact (Tier 3) unless "
                "it encodes structural invariant; not incidental implementation."
            ),
            invariant_links=["HISTORICAL_STEWARD_CULTURE", "CULTURAL_CONTINUITY"],
            purpose_links=["steward lineage"],
            evidence_that_would_change=["Structural invariant encoding would elevate to Tier 1"],
            consequences=["Confusing culture with constitution blocks legitimate evolution"],
        ),
    }


def test_reference_lattice_canonical_tiers() -> None:
    lattice = get_reference_lattice()
    assert lattice["artifact_a"] == 0
    assert lattice["artifact_b"] == 2
    assert lattice["artifact_c"] == 3


def test_significance_judgment_passes_with_canonical_answers() -> None:
    runtime = SignificanceJudgmentRuntime()
    result = runtime.evaluate(_passing_answers())
    assert result.score == 1.0
    assert result.passed is True
    assert not result.failures
    assert not result.rationale_gaps
    assert not result.invariant_mislinks


def test_significance_judgment_fails_on_wrong_tier() -> None:
    answers = _passing_answers()
    answers["artifact_b"] = answers["artifact_b"].model_copy(update={"tier": 4})
    result = SignificanceJudgmentRuntime().evaluate(answers)
    assert "artifact_b" in result.failures
    assert result.passed is False


def test_significance_judgment_artifact_a_accepts_tier_1() -> None:
    answers = _passing_answers()
    answers["artifact_a"] = answers["artifact_a"].model_copy(
        update={
            "tier": 1,
            "rationale": (
                "Structural emergency bypass with logged authority is Tier 1 control, not "
                "Tier 0 prohibition, but still risks hidden authority and anti-capture failure."
            ),
        }
    )
    result = SignificanceJudgmentRuntime().evaluate(answers)
    assert "artifact_a" not in result.failures
    assert result.passed is True


def test_significance_judgment_requires_invariant_links() -> None:
    answers = _passing_answers()
    answers["artifact_a"] = answers["artifact_a"].model_copy(update={"invariant_links": []})
    result = SignificanceJudgmentRuntime().evaluate(answers)
    assert "artifact_a" in result.invariant_mislinks
    assert result.passed is False


def test_significance_judgment_pass_threshold() -> None:
    assert SIGNIFICANCE_JUDGMENT_PASS_SCORE == 0.67


def test_submit_and_load_significance_judgment(csr: ConstitutionalStateRuntime) -> None:
    state = seed_passing_significance_judgment(csr)
    assert state.passed is True
    assert state.last_result is not None
    assert state.last_result.score == 1.0


def test_succession_significance_gates(csr: ConstitutionalStateRuntime) -> None:
    seed_passing_significance_judgment(csr)
    assert succession_significance_judgment_ready(csr)[0] is True
    assert succession_significance_continuity_ready(csr)[0] is True
    assert succession_significance_evolution_ready(csr)[0] is True
    ready, message = check_succession_readiness(csr)
    assert ready is True
    assert "satisfied" in message


def test_succession_blocked_without_significance_judgment(
    csr: ConstitutionalStateRuntime,
) -> None:
    blocked, reasons = succession_blocked(_dashboard(), _fitness(), csr=csr)
    assert blocked is True
    assert any("significance" in reason for reason in reasons)


def test_succession_ready_requires_significance_when_csr_present(
    csr: ConstitutionalStateRuntime,
) -> None:
    from tests.constitutional.test_hiddenness_runtime import _all_answers, _seed_mission

    from constitutional.hiddenness.hiddenness_runtime import HiddennessRuntime, load_hiddenness_state
    from constitutional.runtime.mission_fidelity_interactive import submit_mission_fidelity_answers
    from constitutional.runtime.mission_fidelity_runtime import MissionFidelityRuntime
    from constitutional.runtime.reconstructability_dashboard import build_reconstructability_dashboard

    _seed_mission(csr)
    submit_mission_fidelity_answers(csr, _all_answers())
    MissionFidelityRuntime(csr).run_test()
    HiddennessRuntime(csr).run_audit()
    now = datetime.now(UTC)
    dashboard = build_reconstructability_dashboard(csr, snapshot_at=now, version=1)
    dashboard = dashboard.model_copy(
        update={
            "steward_independence_score": 0.85,
            "system_survivability_score": 0.85,
            "founder_dependency_index": 0.15,
            "reconstructability_fitness_score": 0.85,
            "implicit_assumptions_required": 0,
            "active_threats": [],
        }
    )
    hiddenness = load_hiddenness_state(csr)
    assert succession_ready(
        dashboard,
        _fitness(),
        interactive_passed=True,
        csr=csr,
        hiddenness=hiddenness,
    ) is False

    seed_passing_significance_judgment(csr)
    from constitutional.salience.judgment_runtime import seed_passing_salience_judgment
    from tests.constitutional.test_hiddenness_runtime import _seed_salience_ledger_for_succession

    seed_passing_salience_judgment(csr)
    _seed_salience_ledger_for_succession(csr)
    assert succession_ready(
        dashboard,
        _fitness(),
        interactive_passed=True,
        csr=csr,
        hiddenness=hiddenness,
    ) is True
