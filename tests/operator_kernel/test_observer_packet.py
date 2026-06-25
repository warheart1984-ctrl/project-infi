"""Tests for Mission #002-grade observer packets."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from constitutional.runtime import ConstitutionalStateRuntime
from operator_kernel.constitutional_task import register_operator_task
from operator_kernel.csr import CSR
from operator_kernel.observer_packet import (
    PACKET_ROOT,
    write_observer_packet_for_task,
)
from operator_kernel.receipts_store import clear_memory_index
from operator_kernel.status_mapping import sync_operator_status_to_csr


@pytest.fixture(autouse=True)
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_memory_index()
    yield


def test_observer_packet_standard_files(monkeypatch: pytest.MonkeyPatch) -> None:
    isolated = ConstitutionalStateRuntime()
    monkeypatch.setattr("operator_kernel.observer_packet.CSR", isolated)
    monkeypatch.setattr("operator_kernel.csr.CSR", isolated)

    task_id = "task-packet-1"
    register_operator_task(isolated, task_id, goal="observer test")
    meta: dict = {"status": "closed"}
    sync_operator_status_to_csr(isolated, task_id, meta)

    packet_dir = write_observer_packet_for_task(task_id)
    assert packet_dir == PACKET_ROOT / task_id

    for name in ("state.json", "receipts.json", "replay.json", "verification.json", "README.md"):
        assert (packet_dir / name).is_file(), f"missing {name}"

    readme = (packet_dir / "README.md").read_text(encoding="utf-8")
    assert task_id in readme
    assert "divergence_detected" in readme

    replay_data = json.loads((packet_dir / "replay.json").read_text(encoding="utf-8"))
    assert replay_data["diverged"] is False
