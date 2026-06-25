"""Tests for operator_kernel receipts_store."""

from __future__ import annotations

from pathlib import Path

import pytest

from constitutional.runtime import TransitionReceiptV2
from operator_kernel.constitutional_task import build_operator_transition_receipt, register_operator_task
from operator_kernel.csr import CSR
from operator_kernel.receipts_store import (
    ALL,
    BY_STATE,
    append_receipt,
    clear_memory_index,
    load_receipts_for_state,
)


@pytest.fixture(autouse=True)
def _isolate_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_memory_index()
    yield
    clear_memory_index()


def _sample_receipt(task_id: str = "task-abc") -> TransitionReceiptV2:
    register_operator_task(CSR, task_id, goal="test")
    return build_operator_transition_receipt(
        CSR,
        task_id,
        from_state="Proposed",
        to_state="Evaluated",
        kind="Decision",
        legal_basis="test",
    )


def test_append_and_load_per_state() -> None:
    receipt = _sample_receipt()
    append_receipt(receipt)

    assert ALL.is_file()
    state_file = BY_STATE / f"operator_task__task-abc.jsonl"
    assert state_file.is_file()

    loaded = load_receipts_for_state("operator_task", "task-abc")
    assert len(loaded) == 1
    assert loaded[0].receipt_id == receipt.receipt_id


def test_emit_operator_transition_appends_to_store() -> None:
    from operator_kernel.constitutional_task import emit_operator_transition

    task_id = "task-store-1"
    register_operator_task(CSR, task_id, goal="store")
    emit_operator_transition(
        CSR,
        task_id,
        to_state="Evaluated",
        kind="Decision",
        legal_basis="test",
    )
    receipts = load_receipts_for_state("operator_task", task_id)
    assert len(receipts) == 1
