"""Reconstructability dashboard v0 — survivability aggregation and receipts."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from constitutional.runtime.constitutional_debt import ConstitutionalDebtState, save_constitutional_debt
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.fitness_risk import ReconstructabilityRiskState, save_reconstructability_risk
from constitutional.runtime.personal_constitutional_state import PersonalConstitutionalState
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF
from constitutional.runtime.reconstructability_dashboard import (
    DASHBOARD_STATE_ID,
    ReconstructabilityDashboardRuntime,
    build_reconstructability_dashboard,
    load_reconstructability_dashboard,
)
from constitutional.runtime.reconstructability_fitness_runtime import (
    FITNESS_STATE_ID,
    ReconstructabilityFitnessState,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.receipts_v2 import is_receipt_v2_complete


@pytest.fixture(autouse=True)
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_domain_memory_index()


@pytest.fixture
def csr(tmp_path: Path) -> ConstitutionalStateRuntime:
    clear_domain_memory_index()
    return ConstitutionalStateRuntime(persist_root=tmp_path)


def _seed_components(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    fitness = ReconstructabilityFitnessState(
        snapshot_at=now,
        version=1,
        fitness_score=0.8,
        stewardship_readiness_score=0.7,
        failed_surfaces=[RF.EVIDENCE_LOSS],
        implicit_assumptions_required=2,
    )
    csr.put_domain_doc(FITNESS_STATE_ID, "reconstructability_fitness", fitness)

    debt = ConstitutionalDebtState(debt_score=0.2, threats=[RF.LINEAGE_BREAK], fitness_penalty=0.05)
    save_constitutional_debt(csr, debt)

    save_reconstructability_risk(
        csr,
        ReconstructabilityRiskState(
            snapshot_at=now,
            reconstructability_risk=0.3,
            fitness_score=0.8,
            stewardship_readiness_score=0.7,
        ),
    )

    personal = PersonalConstitutionalState(
        snapshot_at=now,
        version=1,
        architectural_continuity=0.6,
        capacity_continuity=0.8,
        unexternalized_ideas=2,
        burnout_warnings=1,
        debt_score=0.3,
        threats=[RF.STEWARD_DISCONTINUITY],
        trend="stable",
    )
    csr.register_personal_snapshot(personal)


def test_build_dashboard_survivability_formula(csr: ConstitutionalStateRuntime) -> None:
    _seed_components(csr)
    now = datetime.now(UTC).replace(microsecond=0)
    state = build_reconstructability_dashboard(csr, snapshot_at=now, version=1)

    expected_survivability = min(
        1.0,
        max(
            0.0,
            0.4 * 0.8 + 0.3 * (1.0 - 0.2) + 0.2 * (1.0 - 0.3) + 0.1 * 0.8,
        ),
    )
    assert state.system_survivability_score == pytest.approx(expected_survivability)
    assert state.steward_independence_score == pytest.approx(
        min(1.0, max(0.0, 0.5 * 0.7 + 0.3 * (1.0 - 2 / 10.0) + 0.2 * 0.0))
    )
    assert state.founder_dependency_index == pytest.approx(1.0 - state.steward_independence_score)
    assert RF.EVIDENCE_LOSS in state.failed_surfaces
    assert RF.LINEAGE_BREAK in state.active_threats
    assert state.fitness
    assert state.debt
    assert state.risk
    assert state.personal


def test_runtime_persists_and_emits_receipt(csr: ConstitutionalStateRuntime) -> None:
    _seed_components(csr)
    runtime = ReconstructabilityDashboardRuntime(csr)
    state = runtime.update_snapshot()
    loaded = load_reconstructability_dashboard(csr)
    assert loaded.version == state.version
    receipts = csr.observation_receipts_for(DASHBOARD_STATE_ID)
    assert len(receipts) == 1
    assert is_receipt_v2_complete(receipts[0])
    assert receipts[0].runtime == "ReconstructabilityDashboardRuntime"


def test_dashboard_version_increments(csr: ConstitutionalStateRuntime) -> None:
    _seed_components(csr)
    runtime = ReconstructabilityDashboardRuntime(csr)
    first = runtime.update_snapshot()
    second = runtime.update_snapshot()
    assert second.version == first.version + 1
