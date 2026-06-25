"""Tests for URG mission CSR bridge."""

from __future__ import annotations

from pathlib import Path

import pytest

from constitutional.runtime import ConstitutionalStateRuntime
from src.ugr.mission.csr_bridge import (
    register_mission_state,
    replay_mission_state,
    sync_mission_finalize_to_csr,
    sync_mission_open_to_csr,
)


@pytest.fixture
def csr(tmp_path: Path) -> ConstitutionalStateRuntime:
    return ConstitutionalStateRuntime(persist_root=tmp_path / "csr")


def test_mission_happy_path_to_closed(csr: ConstitutionalStateRuntime) -> None:
    mission_id = "mission-001"
    register_mission_state(csr, mission_id, ingress={"tenant_id": "t1", "operator_id": "op1"})
    sync_mission_open_to_csr(csr, mission_id, ingress={"tenant_id": "t1"})
    sync_mission_finalize_to_csr(
        csr,
        mission_id,
        urg_status="ok",
        mission_receipt={"ingress_stamp_hash": "abc123"},
        summary="completed",
    )
    state = csr.get_state(mission_id)
    assert state.current_state == "Closed"
    replay = replay_mission_state(csr, mission_id)
    assert replay.diverged is False


def test_mission_blocked_path(csr: ConstitutionalStateRuntime) -> None:
    mission_id = "mission-blocked"
    sync_mission_open_to_csr(csr, mission_id)
    sync_mission_finalize_to_csr(csr, mission_id, urg_status="blocked", summary="invariant fail")
    state = csr.get_state(mission_id)
    assert state.current_state == "Closed"
    assert len(csr.receipts_for(mission_id)) >= 4
