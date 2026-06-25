"""Tests for constitutional bootloader (governance_gate)."""

from __future__ import annotations

import os

import pytest

from constitutional.runtime import ConstitutionalStateRuntime, StateObject
from constitutional.runtime.governance_gate import (
    GovernanceGateFailed,
    assert_constitutional_boot,
    check_closed_states_have_receipts,
    check_replay_for_all,
    governance_gate,
    run_boot_checks_for_csr,
)
from operator_kernel.constitutional_task import register_operator_task
from operator_kernel.status_mapping import sync_operator_status_to_csr


@pytest.fixture(autouse=True)
def _enable_boot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CONSTITUTIONAL_BOOT_SKIP", raising=False)
    import constitutional.runtime.governance_gate as gg

    monkeypatch.setattr(gg, "_BOOT_COMPLETED", False)


def test_empty_csr_passes_boot() -> None:
    csr = ConstitutionalStateRuntime()
    report = run_boot_checks_for_csr("test", csr, hydrate=False)
    assert report.ok


def test_divergent_closed_state_fails_replay() -> None:
    csr = ConstitutionalStateRuntime()
    csr.register_state(StateObject(state_id="bad", state_type="operator_task", current_state="Closed"))
    failures = check_replay_for_all(csr)
    assert any("divergence" in f for f in failures)


def test_closed_without_receipts_fails() -> None:
    csr = ConstitutionalStateRuntime()
    csr.register_state(StateObject(state_id="bad", state_type="operator_task", current_state="Closed"))
    failures = check_closed_states_have_receipts(csr)
    assert failures


def test_happy_path_operator_task_passes() -> None:
    csr = ConstitutionalStateRuntime()
    task_id = "boot-ok"
    register_operator_task(csr, task_id, goal="boot test")
    meta = {"status": "closed"}
    sync_operator_status_to_csr(csr, task_id, meta)
    report = run_boot_checks_for_csr("operator", csr, hydrate=False)
    assert report.ok, report.failures


def test_assert_constitutional_boot_raises() -> None:
    csr = ConstitutionalStateRuntime()
    csr.register_state(StateObject(state_id="bad", state_type="mission", current_state="Closed"))
    with pytest.raises(GovernanceGateFailed):
        assert_constitutional_boot(csrs=[("test", csr)], hydrate=False)


def test_governance_gate_aggregate() -> None:
    csr = ConstitutionalStateRuntime()
    report = governance_gate(csrs=[("ok", csr)], hydrate=False)
    assert report.ok
