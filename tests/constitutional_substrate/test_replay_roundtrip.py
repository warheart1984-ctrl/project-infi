"""Round-trip tests for constitutional_substrate package."""

from __future__ import annotations

from constitutional.runtime import ConstitutionalStateRuntime
from operator_kernel.constitutional_task import advance_operator_happy_path, register_operator_task


def test_csr_register_and_happy_path_replay() -> None:
    csr = ConstitutionalStateRuntime()
    task_id = "task-test-001"
    register_operator_task(csr, task_id, goal="smoke")
    advance_operator_happy_path(
        csr,
        task_id,
        target="Closed",
        kind="Closure",
        legal_basis="test",
    )
    replay = csr.replay(task_id)
    assert not replay.diverged
    assert csr.get_state(task_id).current_state == "Closed"
    assert len(csr.receipts_for(task_id)) == 5
