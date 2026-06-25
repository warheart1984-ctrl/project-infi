"""Tests for ECK-2 dual-pipeline epistemic kernel."""

from __future__ import annotations

import pytest

from constitutional.core.articles import ECK2_MIN_DRIFT_SYMMETRY_INDEX
from constitutional.eck2 import (
    ECK2Runtime,
    check_eck2_succession_gate,
    eck2_from_csr,
    load_eck2_pipeline,
)
from constitutional.eck2.governance import succession_eck2_dual_pipeline_ready
from constitutional.jpss import JPSSFormationRuntime
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


def _steward_inputs(**overrides):
    defaults = {
        "decision_id": "eck2-dec-001",
        "available_signals": ["fitness", "continuity"],
        "expected_signals": ["reconstructability"],
        "constraints_active": ["article_r"],
        "environmental_factors": ["succession_pressure"],
        "outcome": "observe",
        "rationale": "Dual-pipeline kernel audit.",
        "expected_result": "observe",
        "success": True,
    }
    defaults.update(overrides)
    return defaults


def test_eck2_kernel_runs_dual_pipeline(csr: ConstitutionalStateRuntime) -> None:
    result = eck2_from_csr(csr).run(_steward_inputs())
    assert result.formation.decision_id == "eck2-dec-001"
    assert result.reconstruction.reconstructable
    assert result.drift_symmetry.symmetry_index >= ECK2_MIN_DRIFT_SYMMETRY_INDEX
    assert result.eck1_continuity is not None


def test_eck2_runtime_persists_pipeline(csr: ConstitutionalStateRuntime) -> None:
    ECK2Runtime(csr).run(_steward_inputs())
    loaded = load_eck2_pipeline(csr)
    assert loaded is not None
    assert loaded.reconstruction.judgment is not None
    assert loaded.reconstruction.judgment.outcome == "observe"


def test_eck2_reconstruction_after_jpss_only(csr: ConstitutionalStateRuntime) -> None:
    cycle = JPSSFormationRuntime(csr).run(_steward_inputs(decision_id="eck2-dec-002"))
    reconstruction = eck2_from_csr(csr).reconstruction.reconstruct(cycle.decision_id)
    assert reconstruction.reconstructable
    assert reconstruction.environment is not None
    assert reconstruction.salience is not None


def test_eck2_succession_gate_blocks_without_pipeline(csr: ConstitutionalStateRuntime) -> None:
    ready, message = check_eck2_succession_gate(csr)
    assert ready is False
    assert "JPSS" in message or "ECK-1" in message or "ECK-2" in message


def test_succession_eck2_governance_skips_when_no_pipeline(csr: ConstitutionalStateRuntime) -> None:
    ok, reasons = succession_eck2_dual_pipeline_ready(csr)
    assert ok is True
    assert reasons == []


def test_eck2_threshold_matches_spec() -> None:
    assert ECK2_MIN_DRIFT_SYMMETRY_INDEX == 0.80


def test_article_jpss_registered() -> None:
    from constitutional import constitutional_registry
    from constitutional.core.articles import ARTICLE_JPSS_ID

    article = constitutional_registry.get_article(ARTICLE_JPSS_ID)
    assert article is not None
    assert article["non_derogable"] is True
