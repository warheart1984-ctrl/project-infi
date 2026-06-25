"""Purpose continuity — P-F taxonomy, mission fidelity, and amendment tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from constitutional.core.articles import (
    ARTICLE_P_REFERENCE,
    PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE_ID,
    PURPOSE_CONTINUITY_INDEX_THRESHOLD,
    PURPOSE_CONTINUITY_INVARIANT,
)
from constitutional.purpose.purpose_continuity_amendment import (
    PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE,
    build_purpose_continuity_amendment_proposal,
    maybe_trigger_purpose_continuity_amendment,
    should_trigger_purpose_continuity_amendment,
)
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.mission_fidelity_runtime import (
    MISSION_STATEMENT_STATE_ID,
    MissionFidelityRuntime,
    MissionFidelityState,
    MissionStatementState,
    load_mission_fidelity_state,
)
from constitutional.runtime.purpose_failures import ALL_PURPOSE_FAILURES, PurposeFailureClass as PF
from constitutional.runtime.receipts_v2 import is_receipt_v2_complete
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.runtime_charter import RUNTIME_CHARTER


@pytest.fixture(autouse=True)
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_domain_memory_index()


@pytest.fixture
def csr(tmp_path: Path) -> ConstitutionalStateRuntime:
    clear_domain_memory_index()
    runtime = ConstitutionalStateRuntime(persist_root=tmp_path)
    runtime.register_invariant(PURPOSE_CONTINUITY_INVARIANT, ARTICLE_P_REFERENCE)
    runtime.register_invariant(
        "CRITICAL_SYSTEMS_MUST_REMAIN_RECONSTRUCTABLE",
        "Article R",
    )
    return runtime


def _seed_mission(csr: ConstitutionalStateRuntime) -> None:
    csr.put_domain_doc(
        MISSION_STATEMENT_STATE_ID,
        "mission_statement",
        MissionStatementState(
            text=(
                "Enable independent stewards to reconstruct and operate governed systems "
                "without founder assistance while preserving constitutional meaning."
            ),
            invariant_rationale="Purpose must survive steward discontinuity.",
            founding_context=(
                "Born from observer-reproducible proof requirements and constitutional substrate design."
            ),
        ),
    )


def test_all_pf_classes_exist() -> None:
    from constitutional.runtime.purpose_failures import PurposeFailureClass

    assert len(PurposeFailureClass) == 10
    assert len(ALL_PURPOSE_FAILURES) == 10
    assert PF.MISSION_AMNESIA.value == "P-F3 MissionAmnesia"


def test_mission_fidelity_runtime_charter() -> None:
    assert len(RUNTIME_CHARTER["MissionFidelityRuntime"]) == 10


def test_mission_fidelity_fails_without_mission_statement(csr: ConstitutionalStateRuntime) -> None:
    state = MissionFidelityRuntime(csr).run_test()
    assert PF.MISSION_AMNESIA in state.failed_surfaces
    assert state.mission_legibility_score == 0.0
    assert state.purpose_continuity_index < PURPOSE_CONTINUITY_INDEX_THRESHOLD
    receipts = csr.observation_receipts_for(state.state_id)
    assert len(receipts) == 1
    assert is_receipt_v2_complete(receipts[0])


def test_mission_fidelity_passes_with_legible_mission(csr: ConstitutionalStateRuntime) -> None:
    _seed_mission(csr)
    state = MissionFidelityRuntime(csr).run_test()
    assert PF.MISSION_AMNESIA not in state.failed_surfaces
    assert state.mission_legibility_score == 1.0
    loaded = load_mission_fidelity_state(csr)
    assert loaded.version == state.version


def test_purpose_continuity_amendment_template() -> None:
    assert PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE["template_id"] == PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE_ID
    assert "Article P" in PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE["problem_statement"]


def test_amendment_triggers_on_low_purpose_continuity(csr: ConstitutionalStateRuntime) -> None:
    state = MissionFidelityRuntime(csr).run_test()
    assert should_trigger_purpose_continuity_amendment(state)
    opened = maybe_trigger_purpose_continuity_amendment(csr, state)
    assert opened
    proposal = build_purpose_continuity_amendment_proposal(state)
    assert proposal["evidence"]["failed_surfaces"]
