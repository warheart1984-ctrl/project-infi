"""Tests for Personal Constitutional State v0."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from constitutional.runtime import (
    ConstitutionalStateRuntime,
    PersonalConstitutionalState,
    PersonalConstitutionalStateRuntime,
    ReconstructabilityFailureClass,
    compute_debt_score,
)
from constitutional.runtime.burnout_runtime import BurnoutState
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.personal_constitutional_state import burnout_health_score
from constitutional.runtime.personal_continuity_runtime import IdeaState
from constitutional.runtime.receipts_v2 import is_receipt_v2_complete
from operator_kernel.personal_gate import PersonalGateDecision, evaluate_personal_gate


@pytest.fixture
def csr(tmp_path: Path) -> ConstitutionalStateRuntime:
    clear_domain_memory_index()
    return ConstitutionalStateRuntime(persist_root=tmp_path)


def _idea(
    *,
    foundational: bool,
    externalized: bool,
    idea_id: str = "idea-1",
) -> IdeaState:
    return IdeaState(
        state_id=idea_id,
        title="test idea",
        status="seed",
        foundational=foundational,
        evidence_links=["doc-1"] if externalized else [],
        last_updated_at=datetime.now(UTC),
    )


def _register_idea(csr: ConstitutionalStateRuntime, idea: IdeaState) -> None:
    csr.put_domain_doc(idea.state_id, "idea", idea)


def test_pcs_invariants_reject_perfect_capacity_with_warnings() -> None:
    with pytest.raises(ValueError, match="PCS-2"):
        PersonalConstitutionalState(
            snapshot_at=datetime.now(UTC),
            version=1,
            architectural_continuity=0.8,
            capacity_continuity=1.0,
            unexternalized_ideas=0,
            burnout_warnings=1,
            debt_score=0.5,
            trend="stable",
        )


def test_update_snapshot_emits_complete_observation_receipt(csr: ConstitutionalStateRuntime) -> None:
    _register_idea(csr, _idea(foundational=True, externalized=True, idea_id="i1"))
    pcs = PersonalConstitutionalStateRuntime(csr)

    state = pcs.update_snapshot(snapshot_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC))

    assert state.version == 1
    assert state.architectural_continuity == 1.0
    assert state.unexternalized_ideas == 0
    assert state.debt_score == compute_debt_score(0, 0)

    receipts = csr.observation_receipts_for(state.state_id)
    assert len(receipts) == 1
    assert is_receipt_v2_complete(receipts[0])


def test_unexternalized_foundational_ideas_reduce_architectural_continuity(
    csr: ConstitutionalStateRuntime,
) -> None:
    _register_idea(csr, _idea(foundational=True, externalized=False, idea_id="i1"))
    _register_idea(csr, _idea(foundational=True, externalized=True, idea_id="i2"))
    pcs = PersonalConstitutionalStateRuntime(csr)

    state = pcs.update_snapshot(snapshot_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC))

    assert state.unexternalized_ideas == 1
    assert state.architectural_continuity == 0.5
    assert state.debt_score == compute_debt_score(1, 0)
    assert ReconstructabilityFailureClass.EVIDENCE_LOSS in state.threats


def test_burnout_snapshot_triggers_warning_and_low_capacity(csr: ConstitutionalStateRuntime) -> None:
    csr.set_burnout_latest(
        BurnoutState(
            state_id="burnout__latest",
            snapshot_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
            sleep_quality=0.2,
            stress_level=0.9,
            cognitive_load=0.9,
            meeting_load=0.8,
            recovery_index=0.1,
            trend="worsening",
        )
    )
    pcs = PersonalConstitutionalStateRuntime(csr)

    state = pcs.update_snapshot(snapshot_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC))

    assert state.burnout_warnings == 1
    assert state.capacity_continuity < 0.4
    assert burnout_health_score(csr.get_state_doc("burnout__latest")) < 0.4


def test_personal_gate_blocks_on_low_capacity_and_high_debt(csr: ConstitutionalStateRuntime) -> None:
    _register_idea(csr, _idea(foundational=True, externalized=False, idea_id="i1"))
    _register_idea(csr, _idea(foundational=True, externalized=False, idea_id="i2"))
    _register_idea(csr, _idea(foundational=True, externalized=False, idea_id="i3"))
    csr.set_burnout_latest(
        BurnoutState(
            state_id="burnout__latest",
            snapshot_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
            sleep_quality=0.2,
            stress_level=0.9,
            cognitive_load=0.9,
            meeting_load=0.8,
            recovery_index=0.1,
            trend="worsening",
        )
    )
    pcs = PersonalConstitutionalStateRuntime(csr)

    decision = evaluate_personal_gate(csr=csr, pcs=pcs)

    assert isinstance(decision, PersonalGateDecision)
    assert decision.level == "block"
    assert decision.allow is False


def test_trend_worsening_when_debt_increases(csr: ConstitutionalStateRuntime) -> None:
    pcs = PersonalConstitutionalStateRuntime(csr)

    pcs.update_snapshot(snapshot_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC))
    _register_idea(csr, _idea(foundational=True, externalized=False, idea_id="i1"))
    _register_idea(csr, _idea(foundational=True, externalized=False, idea_id="i2"))
    _register_idea(csr, _idea(foundational=True, externalized=False, idea_id="i3"))

    state = pcs.update_snapshot(snapshot_at=datetime(2026, 6, 23, 13, 0, tzinfo=UTC))

    assert state.trend == "worsening"
    assert state.version == 2
