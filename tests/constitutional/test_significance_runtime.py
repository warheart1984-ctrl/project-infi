"""Tests for Significance Runtime v0, stability, pressure, and competence stack."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from constitutional.core.articles import SIGNIFICANCE_HEALTH_THRESHOLD
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.significance.competence_stack import constitutional_competence_stack_heartbeat
from constitutional.significance.significance_pressure import apply_significance_pressure
from constitutional.significance.significance_runtime import SignificanceRuntime
from constitutional.significance.significance_stability_runtime import SignificanceStabilityRuntime


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


def test_significance_runtime_scan(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    state = SignificanceRuntime(csr).run_scan(snapshot_at=now)
    assert 0.0 <= state.significance_health_index <= 1.0
    assert state.version == 1


def test_significance_stability_runtime(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    SignificanceRuntime(csr).run_scan(snapshot_at=now)
    stability = SignificanceStabilityRuntime(csr).run(snapshot_at=now)
    assert 0.0 <= stability.stability_index <= 1.0


def test_significance_pressure_opens_amendment_on_low_health(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    significance = SignificanceRuntime(csr).run_scan(snapshot_at=now)
    if significance.significance_health_index >= SIGNIFICANCE_HEALTH_THRESHOLD:
        significance.significance_health_index = SIGNIFICANCE_HEALTH_THRESHOLD - 0.1
    apply_significance_pressure(csr, significance, opened_at=now)
    from pydantic import BaseModel, Field

    class Triggers(BaseModel):
        state_id: str = "significance_amendment_triggers__pending"
        state_type: str = "significance_amendment_triggers"
        triggers: list[dict[str, str]] = Field(default_factory=list)

    doc = csr.get_domain_doc("significance_amendment_triggers__pending", Triggers)
    assert len(doc.triggers) >= 1


def test_competence_stack_heartbeat(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    result = constitutional_competence_stack_heartbeat(csr, snapshot_at=now)
    assert "significance" in result
    assert "significance_stability" in result
    assert "decision_environment" in result
    assert "succession_ok" in result
