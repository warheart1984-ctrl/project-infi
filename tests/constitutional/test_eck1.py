"""Tests for ECK-1 epistemic continuity kernel."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from constitutional.core.articles import (
    ARTICLE_Q2_ID,
    ARTICLE_Q_ID,
    ECK1_MIN_PRIOR_DRIFT_INDEX,
    ECK1_MIN_SALIENCE_INDEX,
)
from constitutional.eck1 import (
    ECK1,
    ECK1ContinuitySuite,
    ECK1Runtime,
    check_eck1_succession_gate,
    eck1_from_csr,
    perception_transition,
)
from constitutional.eck1.models import EnvironmentState, PriorState
from constitutional.eck1.runtime import ECK1Registers
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.runtime import ConstitutionalStateRuntime


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


def test_perception_transition_derives_salience() -> None:
    priors = PriorState(
        expected_signals=["fitness", "hiddenness"],
        expected_risks=["drift"],
        ignored_possibilities=["noise"],
    )
    env = EnvironmentState(failure_modes_feared=["succession_failure"])
    salience = perception_transition(priors, env)
    assert "fitness" in salience.primary_signals
    assert "succession_failure" in salience.primary_signals
    assert "drift" in salience.secondary_signals


def test_eck1_minimal_kernel_run(csr: ConstitutionalStateRuntime) -> None:
    kernel = eck1_from_csr(csr)
    result = kernel.run(
        {
            "decision_id": "dec-001",
            "expected_signals": ["reconstructability"],
            "expected_risks": ["hiddenness"],
            "constraints_active": ["article_r"],
            "outcome": "observe",
            "rationale": "Constitutional fitness audit required.",
            "artifact_id": "article_r",
            "tier": 0,
            "significance_rationale": "Core reconstructability doctrine.",
        }
    )
    assert result.artifact_id == "article_r"
    assert result.tier == 0


def test_eck1_runtime_persists_registers(csr: ConstitutionalStateRuntime) -> None:
    runtime = ECK1Runtime(csr)
    pipeline = runtime.run(
        {
            "decision_id": "dec-002",
            "expected_signals": ["mission"],
            "environmental_factors": ["pressure"],
            "outcome": "pass",
            "rationale": "Mission fidelity holds.",
        }
    )
    assert pipeline.judgment.decision_id == "dec-002"
    assert pipeline.salience.primary_signals


def test_eck1_continuity_suite_runs(csr: ConstitutionalStateRuntime) -> None:
    eck1_from_csr(csr).run(
        {
            "decision_id": "dec-003",
            "expected_signals": ["continuity"],
            "outcome": "observe",
            "rationale": "Continuity check.",
        }
    )
    suite = ECK1ContinuitySuite(csr).run()
    assert suite.continuity.prior_drift_index >= 0.0
    assert suite.continuity.salience_index >= 0.0


def test_eck1_succession_gate_empty_csr(csr: ConstitutionalStateRuntime) -> None:
    ready, message = check_eck1_succession_gate(csr)
    assert isinstance(ready, bool)
    assert message


def test_eck1_thresholds_match_spec() -> None:
    assert ECK1_MIN_PRIOR_DRIFT_INDEX == 0.80
    assert ECK1_MIN_SALIENCE_INDEX == 0.80


def test_article_q_registered() -> None:
    from constitutional import constitutional_registry

    article = constitutional_registry.get_article(ARTICLE_Q_ID)
    assert article is not None
    assert article["non_derogable"] is True

    article2 = constitutional_registry.get_article(ARTICLE_Q2_ID)
    assert article2 is not None
