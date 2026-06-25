"""Tests for operator status → constitutional state mapping."""

from __future__ import annotations

import pytest

from constitutional.runtime import ConstitutionalStateRuntime
from operator_kernel.constitutional_task import register_operator_task
from operator_kernel.status_mapping import (
    OPERATOR_STATUS_TO_CONSTITUTIONAL,
    constitutional_target_for_operator_status,
    sync_operator_status_to_csr,
)


def test_mapping_covers_operator_kernel_statuses() -> None:
    for status in ("queued", "planned", "running", "executing", "awaiting_approval", "completed", "failed", "cancelled", "closed"):
        assert status in OPERATOR_STATUS_TO_CONSTITUTIONAL


def test_sync_running_to_evaluated() -> None:
    csr = ConstitutionalStateRuntime()
    task_id = "map-1"
    register_operator_task(csr, task_id, goal="x")
    meta = {"status": "running"}
    sync_operator_status_to_csr(csr, task_id, meta)
    assert csr.get_state(task_id).current_state == "Evaluated"
    assert meta["constitutional_state"] == "Evaluated"


def test_sync_closed_walks_happy_path() -> None:
    csr = ConstitutionalStateRuntime()
    task_id = "map-2"
    register_operator_task(csr, task_id, goal="x")
    meta = {"status": "closed"}
    sync_operator_status_to_csr(csr, task_id, meta)
    assert csr.get_state(task_id).current_state == "Closed"


def test_unknown_status_raises() -> None:
    with pytest.raises(ValueError, match="unknown operator status"):
        constitutional_target_for_operator_status("not_a_status")
