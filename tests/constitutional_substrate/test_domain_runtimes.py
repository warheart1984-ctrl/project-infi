"""Personal continuity + burnout runtimes on shared CSR."""

from __future__ import annotations

from pathlib import Path

import pytest

from constitutional.runtime import ConstitutionalStateRuntime
from constitutional.runtime.burnout_runtime import BurnoutRuntime
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.personal_continuity_runtime import (
    CriticalContextState,
    PersonalContinuityRuntime,
)


@pytest.fixture
def csr(tmp_path: Path) -> ConstitutionalStateRuntime:
    clear_domain_memory_index()
    return ConstitutionalStateRuntime(persist_root=tmp_path)


def test_personal_continuity_idea_and_risk_receipt(csr: ConstitutionalStateRuntime) -> None:
    pc = PersonalContinuityRuntime(csr)
    idea = pc.create_idea("Collapse the stack", foundational=True)
    assert idea.status == "seed"

    risk = pc.assess_continuity_risk()
    assert risk.outputs.status == "Observation"
    assert risk.runtime == "PersonalContinuityRuntime"
    assert csr.domain_receipts_for("personal_continuity__global")

    idea_receipts = csr.domain_receipts_for(idea.state_id)
    assert len(idea_receipts) == 1
    assert idea_receipts[0].outputs.status == "Creation"


def test_burnout_snapshot_and_risk(csr: ConstitutionalStateRuntime) -> None:
    bo = BurnoutRuntime(csr)
    snap = bo.snapshot(
        sleep_quality=0.4,
        stress_level=0.8,
        cognitive_load=0.7,
        meeting_load=0.6,
        recovery_index=0.3,
    )
    assert snap.trend == "stable"

    risk = bo.assess_risk()
    assert risk.outputs.status == "Observation"
    assert "burnout_risk_score" in risk.observation.notes or risk.observation.observed_status


def test_continuity_risk_counts_unexternalized_context(csr: ConstitutionalStateRuntime) -> None:
    from datetime import datetime, timezone

    pc = PersonalContinuityRuntime(csr)
    ctx = CriticalContextState(
        state_id="ctx__1",
        description="If I disappear tomorrow: DNS + TLS",
        reconstruction_difficulty="high",
        externalized=False,
        last_updated_at=datetime.now(timezone.utc),
    )
    csr.put_domain_doc(ctx.state_id, "critical_context", ctx)

    risk = pc.assess_continuity_risk()
    payload_note = risk.observation.notes
    assert payload_note.startswith("sha256:")
