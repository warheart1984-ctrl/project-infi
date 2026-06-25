"""Tests for JPSS-I — integrated adaptive + invariant + stewardship layers."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from constitutional.core.articles import (
    ARTICLE_JPSS_I_ID,
    ECK2_MIN_INVARIANT_DRIFT_INDEX,
)
from constitutional.eck2 import ECK2Runtime, check_eck2_succession_gate
from constitutional.jpss import (
    InvariantDriftFailure,
    InvariantEntry,
    StewardshipClassification,
    StewardshipResponse,
    canonical_passing_responses,
    detect_invariant_drift,
    load_invariant_register,
    run_stewardship_balancing_test,
)
from constitutional.jpss.jpss_i_spec import (
    JPSS_I_INVARIANT_CHAIN,
    JPSS_I_LAYERS,
    JPSS_I_SUCCESSION_REQUIREMENTS,
)
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


def _base_invariants() -> dict[str, list[str]]:
    return {
        "purpose_clauses": ["preserve constitutional continuity"],
        "core_values": ["non-derogable", "reconstructable"],
        "commitments": ["succession gate required"],
        "identity_markers": ["eck-2 dual pipeline"],
        "sacred_constraints": ["never bypass succession gate"],
    }


def _steward_inputs(**overrides):
    defaults = {
        "decision_id": "jpss-i-dec-001",
        "available_signals": ["fitness", "continuity"],
        "expected_signals": ["reconstructability"],
        "constraints_active": ["article_r"],
        "environmental_factors": ["succession_pressure"],
        "outcome": "observe",
        "rationale": "JPSS-I integrated kernel audit.",
        "expected_result": "observe",
        "success": True,
        "invariant_defaults": _base_invariants(),
        "stewardship_responses": canonical_passing_responses(),
    }
    defaults.update(overrides)
    return defaults


def test_jpss_i_spec_layers() -> None:
    assert len(JPSS_I_LAYERS) == 3
    assert len(JPSS_I_INVARIANT_CHAIN) == 5
    assert len(JPSS_I_SUCCESSION_REQUIREMENTS) == 5


def test_invariant_register_append_and_load(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    register = load_invariant_register(csr)
    register.append(
        InvariantEntry(
            timestamp=now,
            steward_id="steward-a",
            **_base_invariants(),
        )
    )
    from constitutional.jpss.invariant_register import save_invariant_register

    save_invariant_register(csr, register)
    loaded = load_invariant_register(csr)
    assert len(loaded.entries) == 1
    assert loaded.latest() is not None
    assert "non-derogable" in loaded.latest().core_values


def test_invariant_drift_detects_erosion(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    register = load_invariant_register(csr)
    register.append(
        InvariantEntry(
            timestamp=now,
            steward_id="steward-a",
            **_base_invariants(),
        )
    )
    from constitutional.jpss.invariant_register import save_invariant_register

    save_invariant_register(csr, register)

    eroded = InvariantEntry(
        timestamp=now,
        steward_id="steward-b",
        purpose_clauses=[],
        core_values=["non-derogable"],
        commitments=["succession gate required"],
        identity_markers=["eck-2 dual pipeline"],
        sacred_constraints=["never bypass succession gate"],
    )
    state = detect_invariant_drift(csr, current_invariants=eroded)
    assert InvariantDriftFailure.PURPOSE_EROSION in state.failed_surfaces
    assert state.drift_index < ECK2_MIN_INVARIANT_DRIFT_INDEX


def test_invariant_drift_clean_when_anchors_preserved(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    register = load_invariant_register(csr)
    base = _base_invariants()
    register.append(InvariantEntry(timestamp=now, steward_id="steward-a", **base))
    from constitutional.jpss.invariant_register import save_invariant_register

    save_invariant_register(csr, register)

    current = InvariantEntry(timestamp=now, steward_id="steward-b", **base)
    state = detect_invariant_drift(csr, current_invariants=current)
    assert state.drift_index == 1.0
    assert not state.failed_surfaces


def test_stewardship_balancing_passes_canonical_responses(csr: ConstitutionalStateRuntime) -> None:
    result = run_stewardship_balancing_test(csr, "steward-a", canonical_passing_responses())
    assert result.passed
    assert result.adaptive_competence
    assert result.invariant_competence
    assert result.balancing_competence
    assert not result.over_adaptation_risk
    assert not result.over_rigidity_risk


def test_stewardship_balancing_fails_over_adaptation(csr: ConstitutionalStateRuntime) -> None:
    responses = canonical_passing_responses()
    responses = [
        StewardshipResponse(scenario_id="I1", classification=StewardshipClassification.MUST_CHANGE)
        if r.scenario_id == "I1"
        else r
        for r in responses
    ]
    result = run_stewardship_balancing_test(csr, "steward-b", responses)
    assert not result.passed
    assert result.over_adaptation_risk


def test_eck2_kernel_includes_jpss_i_layers(csr: ConstitutionalStateRuntime) -> None:
    result = ECK2Runtime(csr).run(_steward_inputs())
    assert result.invariant_drift is not None
    assert result.invariant_drift.drift_index >= ECK2_MIN_INVARIANT_DRIFT_INDEX
    assert result.stewardship_balancing is not None
    assert result.stewardship_balancing.passed


def test_eck2_succession_gate_requires_jpss_i(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.salience.judgment_runtime import seed_passing_salience_judgment
    from constitutional.significance.significance_judgment_runtime import seed_passing_significance_judgment
    from tests.constitutional.test_hiddenness_runtime import (
        _seed_mission,
        _seed_salience_ledger_for_succession,
    )

    _seed_mission(csr)
    seed_passing_significance_judgment(csr)
    seed_passing_salience_judgment(csr)
    _seed_salience_ledger_for_succession(csr)

    ECK2Runtime(csr).run(_steward_inputs())
    ready, message = check_eck2_succession_gate(csr)
    assert ready is True
    assert "satisfied" in message.lower()


def test_article_jpss_i_registered() -> None:
    from constitutional import constitutional_registry

    article = constitutional_registry.get_article(ARTICLE_JPSS_I_ID)
    assert article is not None
    assert article["non_derogable"] is True
